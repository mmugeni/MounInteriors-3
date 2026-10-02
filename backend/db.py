"""
db.py — PostgreSQL connection using Neon free tier.
Handles connection pooling and table creation on startup.
"""

import os
import psycopg2 # type: ignore
from psycopg2.extras import RealDictCursor # pyright: ignore[reportMissingModuleSource]


def database_url() -> str:
    """
    Read DATABASE_URL, forgiving the usual copy-paste extras from Neon's
    Connect window: a leading `psql`, a `DATABASE_URL=` prefix, quotes,
    spaces and line breaks.
    """
    raw = os.environ.get('DATABASE_URL', '')
    url = ''.join(raw.split())                      # drop spaces / line breaks
    for prefix in ('DATABASE_URL=', 'psql'):
        if url.startswith(prefix):
            url = url[len(prefix):]
    url = url.strip('\'"')
    if url.startswith('postgres://'):
        url = 'postgresql://' + url[len('postgres://'):]
    return url


def describe_db_problem(err: Exception = None) -> str:
    """A plain-language reason the database can't be used, with the password hidden."""
    raw = os.environ.get('DATABASE_URL', '')
    if not raw.strip():
        return ('DATABASE_URL is not set for this deployment. Add it in Vercel → Settings → '
                'Environment Variables (tick Production), then redeploy.')
    url = database_url()
    if not url.startswith('postgresql://'):
        return ('DATABASE_URL does not look like a Neon connection string. It should start with '
                f'postgresql:// but starts with "{url[:12]}".')
    try:
        from urllib.parse import urlparse
        parts = urlparse(url)
        host = parts.hostname or '(missing)'
        password = parts.password or ''
    except Exception:
        host, password = '(unreadable)', ''
    if err is None:
        return f'DATABASE_URL looks fine (host {host}).'
    msg = str(err).strip().splitlines()[0] if str(err).strip() else err.__class__.__name__
    if password:
        msg = msg.replace(password, '****')
    hint = ''
    low = msg.lower()
    if 'password authentication failed' in low:
        hint = ' The password in DATABASE_URL is wrong: copy the string again from Neon (Connect → copy).'
    elif 'could not translate host name' in low or 'name or service not known' in low:
        hint = ' The host name is wrong or the Neon project was deleted: copy the string again from Neon.'
    elif 'does not exist' in low and 'database' in low:
        hint = ' The database name at the end of the string is wrong: pick the right database in Neon\'s Connect window.'
    elif 'timeout' in low or 'timed out' in low:
        hint = ' Neon did not answer in time. Check the project is active in the Neon console, then reload.'
    elif 'endpoint' in low and ('disabled' in low or 'not found' in low or 'suspend' in low):
        hint = ' The Neon compute is disabled or missing. Open the project in the Neon console.'
    return f'Could not use the database at {host}: {msg}.{hint}'


def get_connection():
    """Return a new database connection using the DATABASE_URL env variable."""
    return psycopg2.connect(
        database_url(),
        cursor_factory=RealDictCursor,
        connect_timeout=10,
    )


def init_db(retries: int = 3, delay: int = 2):
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
        CREATE TABLE IF NOT EXISTS admin_login_failures (
            id          SERIAL PRIMARY KEY,
            ip          VARCHAR(64)  NOT NULL,
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

    cur.execute("""
        CREATE TABLE IF NOT EXISTS site_settings (
            key         VARCHAR(50)  PRIMARY KEY,
            value       TEXT         NOT NULL,
            updated_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS site_photos (
            path         TEXT         PRIMARY KEY,   -- original photo path in index.html
            replacement  TEXT         NOT NULL,      -- uploaded photo shown instead
            updated_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW()
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS portfolio_items (
            id              SERIAL PRIMARY KEY,
            title           VARCHAR(255) NOT NULL,
            category        VARCHAR(50)  NOT NULL,
            category_label  VARCHAR(100) NOT NULL,
            meta            VARCHAR(255) NOT NULL DEFAULT '',  -- e.g. "Remera, Kigali · 2025"
            media           TEXT         NOT NULL DEFAULT '',
            media_type      VARCHAR(10)  NOT NULL DEFAULT 'image',
            visible         BOOLEAN      NOT NULL DEFAULT TRUE,
            sort_order      INTEGER      NOT NULL DEFAULT 0,
            created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
            updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
        );
    """)

    seed_products(cur)
    seed_portfolio(cur)

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


SEED_PORTFOLIO = [
    ('Warm Living Room Transformation', 'living',  'Living Room',      'Kimironko, Kigali · 2024',  'images/warm living room.jpg', 'image'),
    ('Master Bedroom Redesign',         'bedroom', 'Bedroom',          'Remera, Kigali · 2024',     'images/master bedroom.JPG',   'image'),
    ('3D Studio Apartment Concept',     '3d',      '3D Visualization', 'Kimironko, Kigali · 2025',  'images/3d vis3.mp4',          'video'),
    ('Productive Home Office Setup',    'office',  'Home Office',      'Gasabo, Kigali · 2025',     'images/productive.JPG',       'image'),
    ('Earthy Minimalist Lounge',        'living',  'Living Room',      'Nyarugenge, Kigali · 2025', 'images/earthy minimalist.JPG', 'image'),
    ('Dining Room Refresh',             'dining',  'Dining Room',      'Kicukiro, Kigali · 2025',   'images/dining room.JPG',      'image'),
    ('Serene Guest Bedroom',            'bedroom', 'Bedroom',          'Remera, Kigali · 2025',     'images/guest bedroom.JPG',    'image'),
    ('Open Plan Living Area',           'living',  'Living Room',      'Kibagabaga, Kigali · 2025', 'images/open plan.JPG',        'image'),
    ('Creative Studio Corner',          'office',  'Home Office',      'Gasabo, Kigali · 2025',     'images/creative.JPG',         'image'),
    ('Family Dining Space',             'dining',  'Dining Room',      'Nyarugenge, Kigali · 2025', 'images/family.JPG',           'image'),
    ('Contemporary Living Room',        'living',  'Living Room',      'Kicukiro, Kigali · 2025',   'images/contemporary.JPG',     'image'),
    ('Kids Bedroom Design',             'bedroom', 'Bedroom',          'Kimironko, Kigali · 2025',  'images/kids bedroom.JPG',     'image'),
]


def seed_portfolio(cur):
    """Copy the original portfolio projects into the database the first time it is empty."""
    cur.execute("SELECT COUNT(*) AS n FROM portfolio_items")
    if cur.fetchone()['n'] > 0:
        return
    for i, (title, cat, label, meta, media, media_type) in enumerate(SEED_PORTFOLIO, start=1):
        cur.execute("""
            INSERT INTO portfolio_items (title, category, category_label, meta, media, media_type, sort_order)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (title, cat, label, meta, media, media_type, i))
    print(f"Seeded {len(SEED_PORTFOLIO)} portfolio projects.")
