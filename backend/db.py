"""
db.py — PostgreSQL connection using Neon free tier.
Handles connection pooling and table creation on startup.
"""

import os
import psycopg2 # type: ignore
from psycopg2.extras import RealDictCursor # pyright: ignore[reportMissingModuleSource]


def get_connection():
    """Return a new database connection using the DATABASE_URL env variable."""
    return psycopg2.connect(
        os.environ['DATABASE_URL'],
        cursor_factory=RealDictCursor
    )


def init_db(retries: int = 5, delay: int = 3):
    """
    Create the orders and order_items tables if they don't exist.
    Called once when the Flask app starts.
    Retries up to `retries` times with `delay` seconds between attempts
    to handle transient connection failures at container cold-start.
    """
    import time
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            conn = get_connection()
            break
        except Exception as e:
            last_error = e
            print(f"DB connection attempt {attempt}/{retries} failed: {e}")
            if attempt < retries:
                time.sleep(delay)
    else:
        raise RuntimeError(f"Could not connect to database after {retries} attempts: {last_error}")

    cur  = conn.cursor()

    # Several Vercel instances may start at once; only one sets up at a time.
    cur.execute("SELECT pg_advisory_xact_lock(812734)")

    cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id               SERIAL PRIMARY KEY,
            customer_name    VARCHAR(255) NOT NULL,
            phone            VARCHAR(50)  NOT NULL,
            delivery_method  VARCHAR(20)  NOT NULL CHECK (delivery_method IN ('pickup', 'delivery')),
            address          TEXT,
            delivery_note    TEXT,
            total_amount     INTEGER      NOT NULL,   -- stored in RWF (no decimals)
            payment_status   VARCHAR(20)  NOT NULL DEFAULT 'pending',
            order_status     VARCHAR(20)  NOT NULL DEFAULT 'new',
            receipt_url      TEXT,                   -- Firebase Storage download URL
            created_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW()
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            id           SERIAL PRIMARY KEY,
            order_id     INTEGER      NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
            product_name VARCHAR(255) NOT NULL,
            print_name   VARCHAR(255),
            size         VARCHAR(50),
            quantity     INTEGER      NOT NULL,
            price        INTEGER      NOT NULL    -- unit price in RWF
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS quotations (
            id         SERIAL PRIMARY KEY,
            name       VARCHAR(255) NOT NULL,
            email      VARCHAR(255) NOT NULL,
            phone      VARCHAR(100) NOT NULL,
            service    VARCHAR(255) NOT NULL,
            rooms      TEXT,
            budget     VARCHAR(100),
            timeline   VARCHAR(100),
            details    TEXT         NOT NULL,
            status     VARCHAR(50)  NOT NULL DEFAULT 'new',
            created_at TIMESTAMPTZ  NOT NULL DEFAULT NOW()
        );
    """)
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS admin_sessions (
            token       VARCHAR(64)  PRIMARY KEY,
            otp_hash    VARCHAR(64)  NOT NULL,
            attempts    INTEGER      NOT NULL DEFAULT 0,
            verified    BOOLEAN      NOT NULL DEFAULT FALSE,
            expires_at  TIMESTAMPTZ  NOT NULL,
            created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id              SERIAL PRIMARY KEY,
            name            VARCHAR(255) NOT NULL,
            category        VARCHAR(50)  NOT NULL,
            category_label  VARCHAR(100) NOT NULL,
            badge           VARCHAR(50)  NOT NULL DEFAULT '',
            price           INTEGER,                 -- RWF, NULL = not shown
            image           TEXT         NOT NULL DEFAULT '',
            description     TEXT         NOT NULL DEFAULT '',
            sizes           JSONB        NOT NULL DEFAULT '[]'::jsonb,
            prints          JSONB        NOT NULL DEFAULT '[]'::jsonb,
            visible         BOOLEAN      NOT NULL DEFAULT TRUE,
            sort_order      INTEGER      NOT NULL DEFAULT 0,
            created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
            updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS product_images (
            id            SERIAL PRIMARY KEY,
            content_type  VARCHAR(50)  NOT NULL,
            data          BYTEA        NOT NULL,
            created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW()
        );
    """)

    seed_products(cur)

    conn.commit()
    cur.close()
    conn.close()
    print("Database tables ready.")


def seed_products(cur):
    """Copy the original catalogue into the products table the first time it is empty."""
    import json
    cur.execute("SELECT COUNT(*) AS n FROM products")
    if cur.fetchone()['n'] > 0:
        return
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'seed_products.json')
    if not os.path.exists(path):
        return
    with open(path, encoding='utf-8') as f:
        items = json.load(f)
    for p in items:
        cur.execute("""
            INSERT INTO products
              (name, category, category_label, badge, price, image, description,
               sizes, prints, visible, sort_order)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb, %s, %s)
        """, (
            p['name'], p['category'], p['category_label'], p.get('badge', ''),
            p.get('price'), p.get('image', ''), p.get('description', ''),
            json.dumps(p.get('sizes', [])), json.dumps(p.get('prints', [])),
            p.get('visible', True), p.get('sort_order', 0),
        ))
    print(f"Seeded {len(items)} products.")
