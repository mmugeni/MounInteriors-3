"""
app.py — MOUN Digital Platform Flask Backend
Endpoints:
  POST /api/orders                  — Submit a new order (receipt upload + DB save)
  GET  /api/orders                  — Admin: list all orders
  GET  /api/orders/<id>             — Admin: single order with items
  PUT  /api/orders/<id>             — Admin: update payment/order status
  GET  /api/products                — Public: products shown on the website
  GET  /api/admin/products          — Admin: all products, including hidden ones
  POST /api/admin/products          — Admin: add a product
  PUT  /api/admin/products/<id>     — Admin: update a product
  DELETE /api/admin/products/<id>   — Admin: delete a product
  POST /api/admin/images            — Admin: upload a product photo
  GET  /api/images/<id>             — Public: serve an uploaded product photo
  GET  /admin                       — Admin dashboard (password + email OTP protected)
  POST /admin/send-otp              — Send OTP to admin email
  POST /admin/verify-otp            — Verify OTP and issue session token
  GET  /health                      — Health check
"""

import os
import io
import json
import hmac
import hashlib
import smtplib
import secrets
from datetime import datetime, timezone, timedelta
from functools import wraps
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from dotenv import load_dotenv
from psycopg2.extras import Json

from db import get_connection, init_db, describe_db_problem
from storage import upload_receipt

# ── Setup ──────────────────────────────────────────────────────
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-change-in-production')

CORS(app, origins="*", supports_credentials=True)

PUBLIC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'public')

_db_ready = False


@app.before_request
def ensure_database():
    """Create tables (and seed products) once per server instance."""
    global _db_ready
    if _db_ready or request.path in ('/health', '/health/db'):
        return
    try:
        init_db()
        _db_ready = True
    except Exception as e:
        reason = describe_db_problem(e)
        app.logger.error(f"Database setup failed: {reason}")
        return jsonify({'error': 'The database is not reachable.', 'reason': reason}), 503


@app.route('/health/db')
def health_db():
    """Check the database connection and explain any problem in plain language."""
    try:
        conn = get_connection()
        conn.close()
        return jsonify({'database': 'ok', 'detail': describe_db_problem()}), 200
    except Exception as e:
        return jsonify({'database': 'error', 'reason': describe_db_problem(e)}), 503

OTP_MINUTES       = 10
SESSION_HOURS     = 2
MAX_OTP_ATTEMPTS  = 5
MAX_PASSWORD_FAILURES = 10   # wrong passwords allowed per connection...
LOCKOUT_MINUTES       = 15   # ...within this many minutes


def email_code_enabled() -> bool:
    """
    The emailed 6-digit code is off unless EMAIL_LOGIN_CODE is set to on/true/1.
    While it is off, the admin password alone signs in.
    """
    return os.environ.get('EMAIL_LOGIN_CODE', '').strip().lower() in ('1', 'true', 'on', 'yes')


def client_ip() -> str:
    forwarded = request.headers.get('X-Forwarded-For', '')
    return (forwarded.split(',')[0].strip() or request.remote_addr or 'unknown')[:64]


# ── Email helper ───────────────────────────────────────────────

def smtp_send(sender: str, password: str, recipient: str, msg) -> None:
    """
    Send an email. Defaults to Gmail over SSL (port 465). For local testing,
    set SMTP_HOST / SMTP_PORT / SMTP_SECURITY=none to use a catch-all inbox.
    SMTP_SECURITY is one of: ssl (default), starttls, none.
    """
    host     = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
    port     = int(os.environ.get('SMTP_PORT', '465'))
    security = os.environ.get('SMTP_SECURITY', 'ssl').lower()

    if security == 'ssl':
        server = smtplib.SMTP_SSL(host, port, timeout=20)
    else:
        server = smtplib.SMTP(host, port, timeout=20)
        if security == 'starttls':
            server.starttls()
    with server:
        if security != 'none':
            server.login(sender, password)
        server.sendmail(sender, recipient, msg.as_string())

def smtp_settings():
    """Email settings, tidied: Gmail shows App Passwords with spaces, which must be removed."""
    smtp_email    = os.environ.get('SMTP_EMAIL', '').strip()
    smtp_password = ''.join(os.environ.get('SMTP_PASSWORD', '').split()).strip('\'"')
    admin_email   = os.environ.get('ADMIN_EMAIL', '').strip() or smtp_email
    return smtp_email, smtp_password, admin_email


def describe_email_problem(err: Exception = None) -> str:
    """A plain-language reason the login code email could not be sent."""
    smtp_email, smtp_password, admin_email = smtp_settings()
    missing = [k for k, v in (('SMTP_EMAIL', smtp_email), ('SMTP_PASSWORD', smtp_password)) if not v]
    if missing:
        return (f"{' and '.join(missing)} {'is' if len(missing) == 1 else 'are'} not set. Add "
                f"{'it' if len(missing) == 1 else 'them'} in Vercel → Settings → Environment Variables, then redeploy.")
    if err is None:
        return ''
    if isinstance(err, smtplib.SMTPAuthenticationError):
        return (f'Gmail refused to sign in as {smtp_email}. SMTP_PASSWORD must be a 16-letter Gmail App Password '
                f'created on that same account (Google Account → Security → 2-Step Verification → App passwords), '
                f'not the normal Gmail password.')
    if isinstance(err, smtplib.SMTPRecipientsRefused):
        return f'Gmail would not deliver to ADMIN_EMAIL ({admin_email}). Check that address.'
    if isinstance(err, smtplib.SMTPSenderRefused):
        return f'Gmail would not send from SMTP_EMAIL ({smtp_email}). Check that address.'
    if isinstance(err, (OSError, smtplib.SMTPConnectError, smtplib.SMTPServerDisconnected)):
        return f'Could not connect to the mail server: {err}. Try again in a minute.'
    return f'Email failed: {err}'


def send_otp_email(otp_code: str):
    """
    Send OTP to admin email using Gmail SMTP.
    Returns None on success, or a plain-language reason on failure.
    """
    smtp_email, smtp_password, admin_email = smtp_settings()

    if not smtp_email or not smtp_password:
        reason = describe_email_problem()
        app.logger.error(reason)
        return reason

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'MOUN Admin — Your verification code: {otp_code}'
        msg['From']    = smtp_email
        msg['To']      = admin_email

        text_body = f"""
MOUN Admin Dashboard — Verification Code

Your one-time code is: {otp_code}

This code expires in 10 minutes.
Do not share this code with anyone.

— MOUN Security
        """.strip()

        html_body = f"""
<!DOCTYPE html>
<html>
<body style="margin:0;padding:0;background:#F5EDE0;font-family:sans-serif;">
  <div style="max-width:480px;margin:40px auto;background:#fff;border-radius:12px;overflow:hidden;">
    <div style="background:#1E150A;padding:24px 32px;">
      <h1 style="color:#C9A97A;font-size:22px;margin:0;font-weight:500;">moun.</h1>
      <p style="color:rgba(245,239,230,0.6);font-size:12px;margin:4px 0 0;">Admin Dashboard</p>
    </div>
    <div style="padding:32px;">
      <p style="color:#1E150A;font-size:15px;margin:0 0 8px;">Your verification code is:</p>
      <div style="background:#F5EDE0;border-radius:10px;padding:20px;text-align:center;margin:16px 0;">
        <span style="font-size:36px;font-weight:700;letter-spacing:10px;color:#1E150A;">{otp_code}</span>
      </div>
      <p style="color:#7A6A52;font-size:13px;margin:0 0 6px;">This code expires in <strong>10 minutes</strong>.</p>
      <p style="color:#7A6A52;font-size:13px;margin:0;">Do not share this code with anyone.</p>
    </div>
    <div style="background:#F5EDE0;padding:16px 32px;text-align:center;">
      <p style="color:#C9A97A;font-size:11px;margin:0;">© 2025 MOUN — Interior Design & Home Decor, Kigali</p>
    </div>
  </div>
</body>
</html>
        """.strip()

        msg.attach(MIMEText(text_body, 'plain'))
        msg.attach(MIMEText(html_body, 'html'))

        smtp_send(smtp_email, smtp_password, admin_email, msg)

        app.logger.info(f"OTP sent to {admin_email}")
        return None

    except Exception as e:
        reason = describe_email_problem(e)
        app.logger.error(f"Failed to send OTP: {reason}")
        return reason


def generate_otp() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def generate_session_token() -> str:
    return secrets.token_hex(32)


def hash_otp(token: str, otp: str) -> str:
    return hmac.new(app.secret_key.encode(), f"{token}:{otp}".encode(), hashlib.sha256).hexdigest()


def clean_expired_sessions(cur):
    cur.execute("DELETE FROM admin_sessions WHERE expires_at < NOW()")


# ── Admin session decorator ────────────────────────────────────
# Sessions live in the database so every server instance
# sees the same logins.

def require_admin_session(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.args.get('session') or request.headers.get('X-Session-Token')
        if not token:
            return jsonify({'error': 'Unauthorised — session required'}), 401
        conn = get_connection(); cur = conn.cursor()
        try:
            cur.execute("SELECT verified, expires_at FROM admin_sessions WHERE token = %s", (token,))
            row = cur.fetchone()
        finally:
            cur.close(); conn.close()
        if not row:
            return jsonify({'error': 'Unauthorised — session required'}), 401
        if not row['verified']:
            return jsonify({'error': 'Unauthorised — OTP not verified'}), 401
        if row['expires_at'] < datetime.now(timezone.utc):
            return jsonify({'error': 'Session expired — please log in again'}), 401
        return f(*args, **kwargs)
    return decorated


# ── Health check ──────────────────────────────────────────────

@app.route('/health')
def health():
    return jsonify({'status': 'ok'}), 200


# ── POST /admin/send-otp ──────────────────────────────────────

@app.route('/admin/send-otp', methods=['POST'])
def send_otp():
    """
    Step 1 of admin login.
    Verifies the password. If EMAIL_LOGIN_CODE is on, sends a 6-digit code to the
    admin email; otherwise signs in straight away.
    Body: { "password": "your-admin-password" }
    """
    data           = request.get_json() or {}
    password       = data.get('password', '')
    admin_password = os.environ.get('ADMIN_PASSWORD', '')
    ip             = client_ip()

    if not admin_password:
        return jsonify({'error': 'ADMIN_PASSWORD is not set. Add it in Vercel → Settings → Environment Variables, then redeploy.'}), 500

    conn = get_connection(); cur = conn.cursor()
    try:
        cur.execute("DELETE FROM admin_login_failures WHERE created_at < NOW() - INTERVAL '1 day'")
        cur.execute(
            "SELECT COUNT(*) AS n FROM admin_login_failures WHERE ip = %s AND created_at > NOW() - %s * INTERVAL '1 minute'",
            (ip, LOCKOUT_MINUTES),
        )
        if cur.fetchone()['n'] >= MAX_PASSWORD_FAILURES:
            conn.commit()
            return jsonify({'error': f'Too many wrong passwords. Wait {LOCKOUT_MINUTES} minutes and try again.'}), 429

        if not hmac.compare_digest(str(password).encode(), admin_password.encode()):
            cur.execute("INSERT INTO admin_login_failures (ip) VALUES (%s)", (ip,))
            conn.commit()
            return jsonify({'error': 'Incorrect password'}), 401

        cur.execute("DELETE FROM admin_login_failures WHERE ip = %s", (ip,))

        if not email_code_enabled():
            session_token = generate_session_token()
            cur.execute(
                "INSERT INTO admin_sessions (token, otp_hash, verified, expires_at) VALUES (%s, '', TRUE, %s)",
                (session_token, datetime.now(timezone.utc) + timedelta(hours=SESSION_HOURS)),
            )
            conn.commit()
            return jsonify({'success': True, 'session_token': session_token, 'message': 'Signed in.'}), 200
        conn.commit()
    finally:
        cur.close(); conn.close()

    otp        = generate_otp()
    temp_token = generate_session_token()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=OTP_MINUTES)

    conn = get_connection(); cur = conn.cursor()
    try:
        clean_expired_sessions(cur)
        cur.execute(
            "INSERT INTO admin_sessions (token, otp_hash, expires_at) VALUES (%s, %s, %s)",
            (temp_token, hash_otp(temp_token, otp), expires_at),
        )
        conn.commit()

        email_problem = send_otp_email(otp)
        if email_problem:
            cur.execute("DELETE FROM admin_sessions WHERE token = %s", (temp_token,))
            conn.commit()
            return jsonify({'error': f'Could not send the login code. {email_problem}'}), 500
    finally:
        cur.close(); conn.close()

    admin_email = smtp_settings()[2]
    masked      = admin_email
    if '@' in admin_email:
        local, domain = admin_email.split('@', 1)
        masked = (local[0] + '***' + local[-1] if len(local) > 2 else '***') + '@' + domain

    return jsonify({
        'success':    True,
        'temp_token': temp_token,
        'email_hint': masked,
        'message':    f'OTP sent to {masked}. Expires in 10 minutes.',
    }), 200


# ── POST /admin/verify-otp ────────────────────────────────────

@app.route('/admin/verify-otp', methods=['POST'])
def verify_otp():
    """
    Step 2 of admin login.
    Verifies OTP and returns a verified session token.
    Body: { "temp_token": "...", "otp": "123456" }
    """
    data       = request.get_json() or {}
    temp_token = data.get('temp_token', '')
    otp_input  = str(data.get('otp', '')).strip()

    conn = get_connection(); cur = conn.cursor()
    try:
        cur.execute(
            "SELECT otp_hash, attempts, verified, expires_at FROM admin_sessions WHERE token = %s FOR UPDATE",
            (temp_token,),
        )
        entry = cur.fetchone()

        if not entry:
            return jsonify({'error': 'Invalid or expired session. Please start again.'}), 401

        if entry['expires_at'] < datetime.now(timezone.utc):
            cur.execute("DELETE FROM admin_sessions WHERE token = %s", (temp_token,))
            conn.commit()
            return jsonify({'error': 'OTP expired. Please request a new one.'}), 401

        if entry['verified']:
            return jsonify({'error': 'Token already used.'}), 400

        if entry['attempts'] >= MAX_OTP_ATTEMPTS:
            cur.execute("DELETE FROM admin_sessions WHERE token = %s", (temp_token,))
            conn.commit()
            return jsonify({'error': 'Too many attempts. Please request a new code.'}), 401

        if not hmac.compare_digest(hash_otp(temp_token, otp_input), entry['otp_hash']):
            cur.execute("UPDATE admin_sessions SET attempts = attempts + 1 WHERE token = %s", (temp_token,))
            conn.commit()
            return jsonify({'error': 'Incorrect OTP. Please try again.'}), 401

        cur.execute(
            "UPDATE admin_sessions SET verified = TRUE, expires_at = %s WHERE token = %s",
            (datetime.now(timezone.utc) + timedelta(hours=SESSION_HOURS), temp_token),
        )
        conn.commit()
    finally:
        cur.close(); conn.close()

    return jsonify({
        'success':       True,
        'session_token': temp_token,
        'message':       'OTP verified. Access granted.',
    }), 200


# ── POST /api/orders ─────────────────────────────────────────

@app.route('/api/orders', methods=['POST'])
def create_order():
    raw = request.form.get('order_data')
    if not raw:
        return jsonify({'error': 'order_data is required'}), 400

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return jsonify({'error': 'order_data must be valid JSON'}), 400

    required = ['customer_name', 'phone', 'delivery_method', 'total_amount', 'items']
    for field in required:
        if not data.get(field):
            return jsonify({'error': f'Missing required field: {field}'}), 400

    if data['delivery_method'] not in ('pickup', 'delivery'):
        return jsonify({'error': 'delivery_method must be pickup or delivery'}), 400

    if data['delivery_method'] == 'delivery' and not data.get('address'):
        return jsonify({'error': 'address is required for delivery orders'}), 400

    items = data['items']
    if not isinstance(items, list) or len(items) == 0:
        return jsonify({'error': 'items must be a non-empty list'}), 400

    receipt_url  = None
    receipt_file = request.files.get('receipt')

    if receipt_file and receipt_file.filename:
        # Use Firebase Storage if credentials are available, otherwise skip receipt storage.
        # Local disk is NOT used — server instances are short-lived.
        firebase_creds = os.environ.get('FIREBASE_CREDENTIALS')
        if firebase_creds:
            try:
                receipt_url = upload_receipt(receipt_file, receipt_file.filename)
            except Exception as e:
                app.logger.error(f"Firebase receipt upload failed: {e}")
                # Non-fatal: order is still saved, receipt just won't be stored
        else:
            app.logger.warning("FIREBASE_CREDENTIALS not set — receipt not stored.")

    conn = get_connection()
    cur  = conn.cursor()

    try:
        cur.execute("""
            INSERT INTO orders
              (customer_name, phone, delivery_method, address, delivery_note,
               total_amount, receipt_url)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            str(data.get('customer_name') or '').strip() or 'Unknown',
            str(data.get('phone') or '').strip() or 'Unknown',
            data['delivery_method'],
            str(data.get('address') or '').strip() or None,
            str(data.get('delivery_note') or '').strip() or None,
            int(data['total_amount']),
            receipt_url,
        ))

        order_id = cur.fetchone()['id']

        for item in items:
            options_str = item.get('options', '')
            print_name  = None
            size        = None
            for part in options_str.split(','):
                part = part.strip()
                if part.lower().startswith('print:'):
                    print_name = part.split(':', 1)[1].strip()
                elif part.lower().startswith('size:'):
                    size = part.split(':', 1)[1].strip()
                elif part.lower().startswith('colour:'):
                    print_name = part.split(':', 1)[1].strip()

            cur.execute("""
                INSERT INTO order_items
                  (order_id, product_name, print_name, size, quantity, price)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                order_id,
                item.get('name', 'Unknown product'),
                print_name,
                size,
                int(item.get('qty', 1)),
                int(item.get('price_int', 0)),
            ))

        conn.commit()

    except Exception as e:
        conn.rollback()
        app.logger.error(f"Database error: {e}")
        return jsonify({'error': 'Failed to save order. Please try again.'}), 500

    finally:
        cur.close()
        conn.close()

    return jsonify({
        'success':     True,
        'order_id':    order_id,
        'receipt_url': receipt_url,
        'message':     'Order saved successfully',
    }), 201


# ── GET /api/orders ──────────────────────────────────────────

@app.route('/api/orders', methods=['GET'])
@require_admin_session
def list_orders():
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("""
        SELECT o.id, o.customer_name, o.phone, o.delivery_method,
               o.address, o.delivery_note, o.total_amount,
               o.payment_status, o.order_status, o.receipt_url,
               o.created_at, COUNT(oi.id) AS item_count
        FROM orders o
        LEFT JOIN order_items oi ON oi.order_id = o.id
        GROUP BY o.id
        ORDER BY o.created_at DESC
    """)
    orders = [dict(row) for row in cur.fetchall()]
    for order in orders:
        if order.get('created_at'):
            order['created_at'] = order['created_at'].isoformat()
    cur.close()
    conn.close()
    return jsonify({'orders': orders}), 200


# ── GET /api/orders/<id> ─────────────────────────────────────

@app.route('/api/orders/<int:order_id>', methods=['GET'])
@require_admin_session
def get_order(order_id):
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("SELECT * FROM orders WHERE id = %s", (order_id,))
    order = cur.fetchone()
    if not order:
        cur.close(); conn.close()
        return jsonify({'error': 'Order not found'}), 404
    order = dict(order)
    if order.get('created_at'):
        order['created_at'] = order['created_at'].isoformat()
    cur.execute("SELECT * FROM order_items WHERE order_id = %s", (order_id,))
    items = [dict(row) for row in cur.fetchall()]
    cur.close(); conn.close()
    return jsonify({'order': order, 'items': items}), 200


# ── PUT /api/orders/<id> ─────────────────────────────────────

@app.route('/api/orders/<int:order_id>', methods=['PUT'])
@require_admin_session
def update_order(order_id):
    data = request.get_json()
    if not data:
        return jsonify({'error': 'JSON body required'}), 400

    valid_payment = ('pending', 'confirmed', 'rejected')
    valid_order   = ('new', 'processing', 'shipped', 'delivered', 'cancelled')
    updates = []; values = []

    if 'payment_status' in data:
        if data['payment_status'] not in valid_payment:
            return jsonify({'error': 'Invalid payment_status'}), 400
        updates.append('payment_status = %s')
        values.append(data['payment_status'])

    if 'order_status' in data:
        if data['order_status'] not in valid_order:
            return jsonify({'error': 'Invalid order_status'}), 400
        updates.append('order_status = %s')
        values.append(data['order_status'])

    if not updates:
        return jsonify({'error': 'Nothing to update'}), 400

    values.append(order_id)
    conn = get_connection(); cur = conn.cursor()
    cur.execute(f"UPDATE orders SET {', '.join(updates)} WHERE id = %s RETURNING id", values)
    updated = cur.fetchone()
    conn.commit(); cur.close(); conn.close()

    if not updated:
        return jsonify({'error': 'Order not found'}), 404
    return jsonify({'success': True, 'order_id': order_id}), 200



# ── Root redirect ──────────────────────────────────────────────
# The frontend is served separately (Vercel / Netlify / GitHub Pages).
# Visiting the backend root redirects to the admin dashboard.
# ── POST /api/quotations ─────────────────────────────────────

@app.route('/api/quotations', methods=['POST'])
def create_quotation():
    data = request.get_json() or {}
    required = ['name', 'email', 'phone', 'service', 'details']
    for field in required:
        if not data.get(field):
            return jsonify({'error': f'Missing required field: {field}'}), 400

    conn = get_connection()
    cur  = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO quotations
              (name, email, phone, service, rooms, budget, timeline, details, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'new')
            RETURNING id
        """, (
            str(data.get('name',     '')).strip(),
            str(data.get('email',    '')).strip(),
            str(data.get('phone',    '')).strip(),
            str(data.get('service',  '')).strip(),
            str(data.get('rooms',    '') or '').strip() or None,
            str(data.get('budget',   '') or '').strip() or None,
            str(data.get('timeline', '') or '').strip() or None,
            str(data.get('details',  '')).strip(),
        ))
        quotation_id = cur.fetchone()['id']
        conn.commit()
    except Exception as e:
        conn.rollback()
        app.logger.error(f"Quotation DB error: {e}")
        return jsonify({'error': 'Failed to save quotation. Please try again.'}), 500
    finally:
        cur.close()
        conn.close()

    _send_quotation_email(quotation_id, data)
    return jsonify({'success': True, 'quotation_id': quotation_id}), 201


def _send_quotation_email(quotation_id: int, data: dict):
    smtp_email, smtp_password, admin_email = smtp_settings()
    if not smtp_email or not smtp_password:
        return
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'MOUN — New Quotation Request #{quotation_id} from {data.get("name", "")}'
        msg['From']    = smtp_email
        msg['To']      = admin_email
        rows = [
            ('Name',     data.get('name',     '—')),
            ('Email',    data.get('email',    '—')),
            ('Phone',    data.get('phone',    '—')),
            ('Service',  data.get('service',  '—')),
            ('Rooms',    data.get('rooms',    '—') or '—'),
            ('Budget',   data.get('budget',   '—') or '—'),
            ('Timeline', data.get('timeline', '—') or '—'),
        ]
        rows_html = ''.join(
            f'<tr><td style="padding:6px 12px;color:#888;font-size:13px"><strong>{k}</strong></td>'
            f'<td style="padding:6px 12px;font-size:13px">{v}</td></tr>'
            for k, v in rows
        )
        html_body = f"""<!DOCTYPE html><html><body style="margin:0;padding:0;background:#F5EDE0;font-family:sans-serif;">
  <div style="max-width:560px;margin:40px auto;background:#fff;border-radius:12px;overflow:hidden;">
    <div style="background:#1E150A;padding:24px 32px;">
      <h1 style="color:#C9A97A;font-size:22px;margin:0;font-weight:500;">moun.</h1>
      <p style="color:rgba(245,239,230,0.6);font-size:12px;margin:4px 0 0;">New Quotation Request #{quotation_id}</p>
    </div>
    <div style="padding:24px 32px;">
      <table style="width:100%;border-collapse:collapse;">{rows_html}</table>
      <div style="margin-top:16px;background:#F5EDE0;border-radius:8px;padding:16px;">
        <p style="font-size:12px;color:#888;margin:0 0 6px;">Project Details</p>
        <p style="font-size:14px;color:#1E150A;margin:0;line-height:1.6;">{data.get('details', '')}</p>
      </div>
      <div style="margin-top:20px;text-align:center;">
        <a href="mailto:{data.get('email', '')}" style="padding:12px 24px;background:#8B6C4A;color:#fff;border-radius:8px;text-decoration:none;font-size:14px;">Reply via Email</a>
      </div>
    </div>
  </div></body></html>"""
        text_body = "\n".join(f"{k}: {v}" for k, v in rows) + f"\n\nDetails:\n{data.get('details', '')}"
        msg.attach(MIMEText(text_body, 'plain'))
        msg.attach(MIMEText(html_body, 'html'))
        smtp_send(smtp_email, smtp_password, admin_email, msg)
    except Exception as e:
        app.logger.error(f"Failed to send quotation email: {e}")


# ── GET /api/quotations ──────────────────────────────────────

@app.route('/api/quotations', methods=['GET'])
@require_admin_session
def list_quotations():
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("""
        SELECT id, name, email, phone, service, rooms, budget, timeline,
               details, status, created_at
        FROM quotations ORDER BY created_at DESC
    """)
    rows = [dict(r) for r in cur.fetchall()]
    for r in rows:
        if r.get('created_at'):
            r['created_at'] = r['created_at'].isoformat()
    cur.close()
    conn.close()
    return jsonify({'quotations': rows}), 200


# ── PUT /api/quotations/<id> ─────────────────────────────────

@app.route('/api/quotations/<int:qid>', methods=['PUT'])
@require_admin_session
def update_quotation(qid):
    data = request.get_json() or {}
    valid = ('new', 'pending', 'contacted', 'closed')
    new_status = data.get('status')
    if new_status not in valid:
        return jsonify({'error': f'status must be one of: {", ".join(valid)}'}), 400
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("UPDATE quotations SET status = %s WHERE id = %s RETURNING id", (new_status, qid))
    updated = cur.fetchone()
    conn.commit(); cur.close(); conn.close()
    if not updated:
        return jsonify({'error': 'Quotation not found'}), 404
    return jsonify({'success': True, 'quotation_id': qid}), 200


# ── Products ──────────────────────────────────────────────────

CATEGORIES = {
    'planters':    'Planters',
    'candles':     'Candles',
    'vases':       'Vases',
    'baskets':     'Baskets',
    'accessories': 'Accessories',
}
BADGE_SUGGESTIONS = ('New', 'Bestseller', 'Popular', 'Limited', 'Handmade')
MAX_BADGE_LENGTH  = 30
IMAGE_TYPES     = {'image/jpeg', 'image/png', 'image/webp'}
MAX_IMAGE_BYTES = 4 * 1024 * 1024   # Vercel rejects request bodies over 4.5 MB
MAX_IMAGE_SIDE  = 1600


def product_to_json(row: dict) -> dict:
    """Shape a products row the way the website's script.js expects it."""
    return {
        'id':            row['id'],
        'name':          row['name'],
        'category':      row['category'],
        'categoryLabel': row['category_label'],
        'badge':         row['badge'] or '',
        'price':         row['price'],
        'image':         row['image'] or '',
        'description':   row['description'] or '',
        'sizes':         row['sizes'] or [],
        'prints':        row['prints'] or [],
        'visible':       row['visible'],
        'sortOrder':     row['sort_order'],
    }


def clean_product(data: dict):
    """Validate a product payload from the admin dashboard. Returns (fields, error)."""
    name = str(data.get('name') or '').strip()
    if not name:
        return None, 'Product name is required.'
    if len(name) > 255:
        return None, 'Product name must be 255 characters or fewer.'

    category = str(data.get('category') or '').strip()
    if category not in CATEGORIES:
        return None, f'Category must be one of: {", ".join(CATEGORIES)}.'

    badge = str(data.get('badge') or '').strip()
    if len(badge) > MAX_BADGE_LENGTH:
        return None, f'Badge must be {MAX_BADGE_LENGTH} characters or fewer.'

    price = data.get('price')
    if price in (None, ''):
        price = None
    else:
        try:
            price = int(str(price).replace(',', '').strip())
        except ValueError:
            return None, 'Price must be a whole number in RWF.'
        if price < 0:
            return None, 'Price cannot be negative.'

    sizes = []
    for s in data.get('sizes') or []:
        value = str((s or {}).get('value') or '').strip()
        if value:
            sizes.append({'value': value[:50], 'available': bool(s.get('available', True))})

    prints = []
    for pr in data.get('prints') or []:
        pname = str((pr or {}).get('name') or '').strip()
        if pname:
            prints.append({
                'name':      pname[:100],
                'image':     str(pr.get('image') or '').strip(),
                'available': bool(pr.get('available', True)),
            })

    try:
        sort_order = int(data.get('sortOrder') or 0)
    except (TypeError, ValueError):
        sort_order = 0

    return {
        'name':           name,
        'category':       category,
        'category_label': CATEGORIES[category],
        'badge':          badge,
        'price':          price,
        'image':          str(data.get('image') or '').strip(),
        'description':    str(data.get('description') or '').strip(),
        'sizes':          Json(sizes),
        'prints':         Json(prints),
        'visible':        bool(data.get('visible', True)),
        'sort_order':     sort_order,
    }, None


@app.route('/api/products', methods=['GET'])
def list_public_products():
    conn = get_connection(); cur = conn.cursor()
    try:
        cur.execute("SELECT * FROM products WHERE visible ORDER BY sort_order, id")
        rows = cur.fetchall()
    finally:
        cur.close(); conn.close()
    resp = jsonify({'products': [product_to_json(r) for r in rows]})
    resp.headers['Cache-Control'] = 'public, max-age=60'
    return resp, 200


@app.route('/api/admin/products', methods=['GET'])
@require_admin_session
def list_admin_products():
    conn = get_connection(); cur = conn.cursor()
    try:
        cur.execute("SELECT * FROM products ORDER BY sort_order, id")
        rows = cur.fetchall()
    finally:
        cur.close(); conn.close()
    return jsonify({
        'products':   [product_to_json(r) for r in rows],
        'categories': CATEGORIES,
        'badges':     list(BADGE_SUGGESTIONS),
        'site_url':   os.environ.get('SITE_URL', '').rstrip('/'),
    }), 200


@app.route('/api/admin/products', methods=['POST'])
@require_admin_session
def create_product():
    fields, err = clean_product(request.get_json() or {})
    if err:
        return jsonify({'error': err}), 400
    conn = get_connection(); cur = conn.cursor()
    try:
        if not fields['sort_order']:
            cur.execute("SELECT COALESCE(MAX(sort_order), 0) + 1 AS n FROM products")
            fields['sort_order'] = cur.fetchone()['n']
        cols = ', '.join(fields)
        vals = ', '.join(['%s'] * len(fields))
        cur.execute(f"INSERT INTO products ({cols}) VALUES ({vals}) RETURNING *", list(fields.values()))
        row = cur.fetchone()
        conn.commit()
    finally:
        cur.close(); conn.close()
    return jsonify({'success': True, 'product': product_to_json(row)}), 201


@app.route('/api/admin/products/<int:pid>', methods=['PUT'])
@require_admin_session
def update_product(pid):
    fields, err = clean_product(request.get_json() or {})
    if err:
        return jsonify({'error': err}), 400
    if not fields['sort_order']:
        del fields['sort_order']
    sets = ', '.join(f"{k} = %s" for k in fields) + ', updated_at = NOW()'
    conn = get_connection(); cur = conn.cursor()
    try:
        cur.execute(f"UPDATE products SET {sets} WHERE id = %s RETURNING *", list(fields.values()) + [pid])
        row = cur.fetchone()
        conn.commit()
    finally:
        cur.close(); conn.close()
    if not row:
        return jsonify({'error': 'Product not found'}), 404
    return jsonify({'success': True, 'product': product_to_json(row)}), 200


@app.route('/api/admin/products/<int:pid>', methods=['DELETE'])
@require_admin_session
def delete_product(pid):
    conn = get_connection(); cur = conn.cursor()
    try:
        cur.execute("DELETE FROM products WHERE id = %s RETURNING id", (pid,))
        row = cur.fetchone()
        conn.commit()
    finally:
        cur.close(); conn.close()
    if not row:
        return jsonify({'error': 'Product not found'}), 404
    return jsonify({'success': True, 'product_id': pid}), 200


@app.route('/api/admin/images', methods=['POST'])
@require_admin_session
def upload_product_image():
    """Store a product photo in the database, resized so pages stay fast."""
    file = request.files.get('image')
    if not file or not file.filename:
        return jsonify({'error': 'Choose a photo to upload.'}), 400
    raw = file.read(MAX_IMAGE_BYTES + 1)
    if len(raw) > MAX_IMAGE_BYTES:
        return jsonify({'error': 'Photo is too large. Use one under 4 MB.'}), 400

    try:
        from PIL import Image, ImageOps
        img = Image.open(io.BytesIO(raw))
        img = ImageOps.exif_transpose(img)
        img.thumbnail((MAX_IMAGE_SIDE, MAX_IMAGE_SIDE))
        out = io.BytesIO()
        if img.mode in ('RGBA', 'LA', 'P'):
            img = img.convert('RGBA')
            img.save(out, 'WEBP', quality=82)
            content_type = 'image/webp'
        else:
            img.convert('RGB').save(out, 'JPEG', quality=82, optimize=True, progressive=True)
            content_type = 'image/jpeg'
        data = out.getvalue()
    except Exception:
        return jsonify({'error': 'That file is not a JPG, PNG or WEBP photo.'}), 400

    if content_type not in IMAGE_TYPES:
        return jsonify({'error': 'Use a JPG, PNG or WEBP photo.'}), 400

    conn = get_connection(); cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO product_images (content_type, data) VALUES (%s, %s) RETURNING id",
            (content_type, data),
        )
        image_id = cur.fetchone()['id']
        conn.commit()
    finally:
        cur.close(); conn.close()
    return jsonify({'success': True, 'url': f'/api/images/{image_id}'}), 201


@app.route('/api/images/<int:image_id>', methods=['GET'])
def get_product_image(image_id):
    conn = get_connection(); cur = conn.cursor()
    try:
        cur.execute("SELECT content_type, data FROM product_images WHERE id = %s", (image_id,))
        row = cur.fetchone()
    finally:
        cur.close(); conn.close()
    if not row:
        return jsonify({'error': 'Image not found'}), 404
    resp = Response(bytes(row['data']), mimetype=row['content_type'])
    resp.headers['Cache-Control'] = 'public, max-age=31536000, immutable'
    return resp


# ── Website content: settings, site photos, portfolio ─────────

PORTFOLIO_CATEGORIES = {
    'living':  'Living Room',
    'bedroom': 'Bedroom',
    'office':  'Home Office',
    'dining':  'Dining Room',
    '3d':      '3D Visualization',
}

# Photos on the website that the dashboard can replace (portfolio and product
# photos are managed in their own tabs). Videos are left out: they are too large
# to upload through Vercel.
SITE_PHOTOS = [
    {'path': 'images/digitalcraft.jpeg',  'label': 'Home page · What We Offer · Home Décor'},
    {'path': 'images/living room.JPG',    'label': 'Home page · What We Offer · Living Room Design'},
    {'path': 'images/bedroom.JPG',        'label': 'Home page · What We Offer · Bedroom Design'},
    {'path': 'images/mouninterior.PNG',   'label': 'Home page · studio photo below Featured Products'},
    {'path': 'images/homedecor1.jpg',     'label': 'About page · header background'},
    {'path': 'images/our story.JPG',      'label': 'About page · Our Story photo'},
]
SITE_PHOTO_PATHS = {p['path'] for p in SITE_PHOTOS}


def clean_whatsapp_number(raw: str):
    """Digits only, with country code. Returns (number, error)."""
    digits = ''.join(ch for ch in str(raw or '') if ch.isdigit())
    if digits.startswith('00'):
        digits = digits[2:]
    if digits.startswith('0') and len(digits) == 10:      # local Rwandan format 07xx xxx xxx
        digits = '250' + digits[1:]
    if not 8 <= len(digits) <= 15:
        return None, 'Enter the WhatsApp number with its country code, e.g. +250 788 123 456.'
    return digits, None


def portfolio_to_json(row: dict) -> dict:
    return {
        'id':            row['id'],
        'title':         row['title'],
        'category':      row['category'],
        'categoryLabel': row['category_label'],
        'meta':          row['meta'] or '',
        'media':         row['media'] or '',
        'mediaType':     row['media_type'],
        'visible':       row['visible'],
        'sortOrder':     row['sort_order'],
    }


def clean_portfolio(data: dict):
    title = str(data.get('title') or '').strip()
    if not title:
        return None, 'Give the project a title.'
    category = str(data.get('category') or '').strip()
    if category not in PORTFOLIO_CATEGORIES:
        return None, f'Category must be one of: {", ".join(PORTFOLIO_CATEGORIES.values())}.'
    media = str(data.get('media') or '').strip()
    if not media:
        return None, 'Add a photo for the project.'
    media_type = 'video' if str(data.get('mediaType')) == 'video' and media.lower().endswith(('.mp4', '.mov')) else 'image'
    try:
        sort_order = int(data.get('sortOrder') or 0)
    except (TypeError, ValueError):
        sort_order = 0
    return {
        'title':          title[:255],
        'category':       category,
        'category_label': PORTFOLIO_CATEGORIES[category],
        'meta':           str(data.get('meta') or '').strip()[:255],
        'media':          media,
        'media_type':     media_type,
        'visible':        bool(data.get('visible', True)),
        'sort_order':     sort_order,
    }, None


def read_site_content(include_hidden: bool):
    conn = get_connection(); cur = conn.cursor()
    try:
        cur.execute("SELECT key, value FROM site_settings")
        settings = {r['key']: r['value'] for r in cur.fetchall()}
        cur.execute("SELECT path, replacement FROM site_photos")
        photos = {r['path']: r['replacement'] for r in cur.fetchall()}
        cur.execute(
            "SELECT * FROM portfolio_items " + ("" if include_hidden else "WHERE visible ") + "ORDER BY sort_order, id"
        )
        portfolio = [portfolio_to_json(r) for r in cur.fetchall()]
    finally:
        cur.close(); conn.close()
    return settings, photos, portfolio


@app.route('/api/site', methods=['GET'])
def public_site_content():
    settings, photos, portfolio = read_site_content(include_hidden=False)
    resp = jsonify({
        'settings':  {'whatsapp_number': settings.get('whatsapp_number', '')},
        'photos':    photos,
        'portfolio': portfolio,
    })
    resp.headers['Cache-Control'] = 'public, max-age=60'
    return resp, 200


@app.route('/api/admin/site', methods=['GET'])
@require_admin_session
def admin_site_content():
    settings, photos, portfolio = read_site_content(include_hidden=True)
    return jsonify({
        'settings':   {'whatsapp_number': settings.get('whatsapp_number', '')},
        'photos':     [dict(p, replacement=photos.get(p['path'], '')) for p in SITE_PHOTOS],
        'portfolio':  portfolio,
        'categories': PORTFOLIO_CATEGORIES,
    }), 200


@app.route('/api/admin/settings', methods=['PUT'])
@require_admin_session
def update_site_settings():
    data = request.get_json() or {}
    number, err = clean_whatsapp_number(data.get('whatsapp_number'))
    if err:
        return jsonify({'error': err}), 400
    conn = get_connection(); cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO site_settings (key, value) VALUES ('whatsapp_number', %s)
            ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = NOW()
        """, (number,))
        conn.commit()
    finally:
        cur.close(); conn.close()
    return jsonify({'success': True, 'whatsapp_number': number}), 200


@app.route('/api/admin/site-photos', methods=['PUT'])
@require_admin_session
def update_site_photo():
    data = request.get_json() or {}
    path = str(data.get('path') or '')
    if path not in SITE_PHOTO_PATHS:
        return jsonify({'error': 'That photo cannot be replaced from the dashboard.'}), 400
    replacement = str(data.get('replacement') or '').strip()
    conn = get_connection(); cur = conn.cursor()
    try:
        if replacement:
            cur.execute("""
                INSERT INTO site_photos (path, replacement) VALUES (%s, %s)
                ON CONFLICT (path) DO UPDATE SET replacement = EXCLUDED.replacement, updated_at = NOW()
            """, (path, replacement))
        else:
            cur.execute("DELETE FROM site_photos WHERE path = %s", (path,))
        conn.commit()
    finally:
        cur.close(); conn.close()
    return jsonify({'success': True, 'path': path, 'replacement': replacement}), 200


@app.route('/api/admin/portfolio', methods=['POST'])
@require_admin_session
def create_portfolio_item():
    fields, err = clean_portfolio(request.get_json() or {})
    if err:
        return jsonify({'error': err}), 400
    conn = get_connection(); cur = conn.cursor()
    try:
        if not fields['sort_order']:
            cur.execute("SELECT COALESCE(MAX(sort_order), 0) + 1 AS n FROM portfolio_items")
            fields['sort_order'] = cur.fetchone()['n']
        cols = ', '.join(fields)
        vals = ', '.join(['%s'] * len(fields))
        cur.execute(f"INSERT INTO portfolio_items ({cols}) VALUES ({vals}) RETURNING *", list(fields.values()))
        row = cur.fetchone()
        conn.commit()
    finally:
        cur.close(); conn.close()
    return jsonify({'success': True, 'item': portfolio_to_json(row)}), 201


@app.route('/api/admin/portfolio/<int:item_id>', methods=['PUT'])
@require_admin_session
def update_portfolio_item(item_id):
    fields, err = clean_portfolio(request.get_json() or {})
    if err:
        return jsonify({'error': err}), 400
    if not fields['sort_order']:
        del fields['sort_order']
    sets = ', '.join(f"{k} = %s" for k in fields) + ', updated_at = NOW()'
    conn = get_connection(); cur = conn.cursor()
    try:
        cur.execute(f"UPDATE portfolio_items SET {sets} WHERE id = %s RETURNING *", list(fields.values()) + [item_id])
        row = cur.fetchone()
        conn.commit()
    finally:
        cur.close(); conn.close()
    if not row:
        return jsonify({'error': 'Project not found'}), 404
    return jsonify({'success': True, 'item': portfolio_to_json(row)}), 200


@app.route('/api/admin/portfolio/<int:item_id>', methods=['DELETE'])
@require_admin_session
def delete_portfolio_item(item_id):
    conn = get_connection(); cur = conn.cursor()
    try:
        cur.execute("DELETE FROM portfolio_items WHERE id = %s RETURNING id", (item_id,))
        row = cur.fetchone()
        conn.commit()
    finally:
        cur.close(); conn.close()
    if not row:
        return jsonify({'error': 'Project not found'}), 404
    return jsonify({'success': True, 'id': item_id}), 200


@app.route('/')
def serve_index():
    """Vercel serves public/index.html directly; this is a fallback."""
    from flask import redirect, send_from_directory
    if os.path.exists(os.path.join(PUBLIC_DIR, 'index.html')):
        return send_from_directory(PUBLIC_DIR, 'index.html')
    return redirect('/admin')


# ── GET /admin ───────────────────────────────────────────────

ADMIN_HTML = r"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
 <title>MOUN — Admin Dashboard</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: system-ui, sans-serif; background: #f5f5f5; color: #222; }
    /* Tab navigation */
    .tab-nav { display: flex; gap: 0; background: #fff; border-bottom: 2px solid #e0e0e0; padding: 0 2rem; }
    .tab-btn { padding: 0.75rem 1.5rem; border: none; background: none; font-size: 0.9rem; font-weight: 500; color: #888; cursor: pointer; border-bottom: 3px solid transparent; margin-bottom: -2px; transition: all 0.2s; }
    .tab-btn:hover { color: #1E150A; }
    .tab-btn.active { color: #8B6C4A; border-bottom-color: #8B6C4A; }
    .tab-panel { display: none; }
    .tab-panel.active { display: block; }
    /* Quotation badges */
    .badge--new-q      { background: #D1ECF1; color: #0C5460; }
    .badge--pending-q  { background: #FFF3CD; color: #856404; }
    .badge--contacted  { background: #CCE5FF; color: #004085; }
    .badge--closed     { background: #D4EDDA; color: #155724; }
    .q-stats { display: flex; gap: 1rem; padding: 1rem 2rem; flex-wrap: wrap; }

    .login-screen {
      min-height: 100vh; background: #1E150A;
      display: flex; align-items: center; justify-content: center; padding: 20px;
    }
    .login-card {
      background: #fff; border-radius: 16px; padding: 40px 36px;
      width: 100%; max-width: 400px; text-align: center;
    }
    .login-logo { font-size: 28px; font-weight: 500; color: #1E150A; margin-bottom: 4px; }
    .login-logo span { color: #8B6C4A; }
    .login-subtitle { font-size: 12px; color: #7A6A52; margin-bottom: 28px; }
    .login-step-title { font-size: 16px; font-weight: 600; color: #1E150A; margin-bottom: 6px; }
    .login-step-sub { font-size: 12px; color: #7A6A52; margin-bottom: 20px; line-height: 1.5; }
    .login-input {
      width: 100%; padding: 12px 16px; border: 1.5px solid #E0D4C0;
      border-radius: 10px; font-size: 14px; margin-bottom: 12px;
      outline: none; transition: border-color 0.2s;
    }
    .login-input:focus { border-color: #8B6C4A; }
    .otp-input { font-size: 28px; font-weight: 700; letter-spacing: 12px; text-align: center; }
    .login-btn {
      width: 100%; padding: 13px; background: #8B6C4A; color: #F5EFE6;
      border: none; border-radius: 10px; font-size: 14px; font-weight: 500;
      cursor: pointer; transition: background 0.2s;
    }
    .login-btn:hover { background: #7A5C3A; }
    .login-btn:disabled { background: #C9B09A; cursor: not-allowed; }
    .login-error {
      background: #FDECEA; color: #B71C1C; border-radius: 8px;
      padding: 10px 14px; font-size: 13px; margin-bottom: 12px; display: none;
    }
    .login-success-msg {
      background: #EAF3DE; color: #2E7D32; border-radius: 8px;
      padding: 10px 14px; font-size: 13px; margin-bottom: 12px; display: none;
    }
    .resend-link {
      font-size: 12px; color: #8B6C4A; cursor: pointer;
      margin-top: 12px; display: inline-block; text-decoration: underline;
    }
    .step-indicator { display: flex; align-items: center; justify-content: center; gap: 8px; margin-bottom: 24px; }
    .step-dot { width: 8px; height: 8px; border-radius: 50%; background: #E0D4C0; }
    .step-dot.active { background: #8B6C4A; }
    .step-dot.done { background: #4CAF50; }

    .dashboard { display: none; }
    .header {
      background: #1E150A; color: #F7F3EE; padding: 1rem 2rem;
      display: flex; align-items: center; justify-content: space-between;
    }
    .header-logo { font-size: 1.2rem; font-weight: 500; color: #C9A97A; }
    .header-right { display: flex; align-items: center; gap: 1rem; }
    .header-sub { font-size: 0.8rem; opacity: 0.6; }
    .logout-btn {
      padding: 0.35rem 0.85rem; background: transparent;
      border: 1px solid rgba(201,169,122,0.4); color: #C9A97A;
      border-radius: 6px; font-size: 0.8rem; cursor: pointer;
    }
    .toolbar {
      padding: 1rem 2rem; display: flex; gap: 1rem;
      align-items: center; background: #fff;
      border-bottom: 1px solid #e0e0e0; flex-wrap: wrap;
    }
    .toolbar select { padding: 0.45rem 0.75rem; border: 1px solid #ccc; border-radius: 6px; font-size: 0.88rem; }
    .toolbar button { padding: 0.45rem 1rem; background: #8B6C4A; color: #fff; border: none; border-radius: 6px; cursor: pointer; font-size: 0.88rem; }
    .stats { display: flex; gap: 1rem; padding: 1rem 2rem; flex-wrap: wrap; }
    .stat-card { background: #fff; border-radius: 8px; padding: 1rem 1.5rem; min-width: 160px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }
    .stat-card .label { font-size: 0.75rem; color: #888; text-transform: uppercase; letter-spacing: 0.06em; }
    .stat-card .value { font-size: 1.6rem; font-weight: 700; color: #1E150A; margin-top: 4px; }
    .table-wrap { padding: 0 2rem 2rem; overflow-x: auto; }
    table { width: 100%; border-collapse: collapse; background: #fff; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }
    th { background: #1E150A; color: #F7F3EE; padding: 0.75rem 1rem; text-align: left; font-size: 0.78rem; text-transform: uppercase; white-space: nowrap; }
    td { padding: 0.75rem 1rem; border-bottom: 1px solid #f0f0f0; font-size: 0.88rem; vertical-align: middle; }
    tr:last-child td { border-bottom: none; }
    tr:hover td { background: #fafafa; }
    .badge { display: inline-block; padding: 2px 8px; border-radius: 20px; font-size: 0.72rem; font-weight: 700; text-transform: uppercase; }
    .badge--pending    { background: #FFF3CD; color: #856404; }
    .badge--confirmed  { background: #D4EDDA; color: #155724; }
    .badge--rejected   { background: #F8D7DA; color: #721C24; }
    .badge--new        { background: #D1ECF1; color: #0C5460; }
    .badge--processing { background: #CCE5FF; color: #004085; }
    .badge--shipped    { background: #E2D9F3; color: #432874; }
    .badge--delivered  { background: #D4EDDA; color: #155724; }
    .badge--cancelled  { background: #F8D7DA; color: #721C24; }
    .receipt-link { color: #8B6C4A; text-decoration: none; font-weight: 600; }
    .receipt-link:hover { text-decoration: underline; }
    .modal-overlay { display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.6); z-index: 100; align-items: center; justify-content: center; }
    .modal-overlay.open { display: flex; }
    .modal { background: #fff; border-radius: 10px; width: 90%; max-width: 640px; max-height: 90vh; overflow-y: auto; padding: 1.5rem; position: relative; }
    .modal h2 { font-size: 1.1rem; margin-bottom: 1rem; color: #1E150A; }
    .modal-close { position: absolute; top: 1rem; right: 1rem; background: none; border: none; font-size: 1.25rem; cursor: pointer; color: #888; }
    .detail-row { display: flex; gap: 0.5rem; margin-bottom: 0.5rem; font-size: 0.88rem; }
    .detail-row strong { min-width: 140px; color: #888; }
    .items-table { width: 100%; border-collapse: collapse; margin-top: 1rem; font-size: 0.85rem; }
    .items-table th { background: #f5f5f5; padding: 0.5rem; text-align: left; font-size: 0.75rem; color: #888; }
    .items-table td { padding: 0.5rem; border-top: 1px solid #f0f0f0; }
    .receipt-img { max-width: 100%; border-radius: 8px; margin-top: 1rem; border: 1px solid #eee; }
    .status-select { padding: 0.3rem 0.5rem; border-radius: 4px; border: 1px solid #ccc; font-size: 0.8rem; }
    .save-btn { padding: 0.3rem 0.65rem; background: #8B6C4A; color: #fff; border: none; border-radius: 4px; font-size: 0.78rem; cursor: pointer; margin-left: 4px; }
    #loading { text-align: center; padding: 3rem; color: #888; }
    #error-msg { color: #c0392b; padding: 1rem 2rem; }
    /* Products tab */
    .pr-work { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 440px); gap: 0; align-items: start; }
    .pr-list { padding: 1rem 2rem 2rem; min-width: 0; }
    .pr-rows { display: flex; flex-direction: column; gap: 2px; background: #fff; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); padding: 6px; }
    .pr-row { display: grid; grid-template-columns: 52px minmax(0,1fr) auto auto; gap: 12px; align-items: center; padding: 8px 10px; border-radius: 8px; cursor: pointer; border: 1px solid transparent; background: none; width: 100%; text-align: left; font: inherit; color: inherit; }
    .pr-row:hover { background: #FBF8F3; }
    .pr-row.selected { background: #FBF8F3; border-color: #E0D4C0; }
    .pr-row img, .pr-thumb-ph { width: 52px; height: 52px; object-fit: cover; border-radius: 8px; background: #EFE6D8; display: block; }
    .pr-name { font-weight: 600; color: #1E150A; }
    .pr-meta { font-size: 0.78rem; color: #7A6A52; }
    .pr-price { font-size: 0.82rem; color: #7A6A52; white-space: nowrap; font-variant-numeric: tabular-nums; }
    .pill { font-size: 0.72rem; padding: 2px 9px; border-radius: 999px; font-weight: 600; white-space: nowrap; }
    .pill--on { background: #D4EDDA; color: #155724; }
    .pill--off { background: #F8D7DA; color: #721C24; }
    .pr-editor { background: #FBF8F3; border-left: 1px solid #E8DFD1; padding: 1.25rem 1.5rem 2rem; display: flex; flex-direction: column; gap: 14px; min-height: 100%; min-width: 0; }
    .pr-editor h3 { font-size: 1.1rem; color: #1E150A; }
    .pr-empty { color: #7A6A52; font-size: 0.9rem; padding: 2rem 0; }
    .pr-field { display: flex; flex-direction: column; gap: 5px; }
    .pr-field > label, .pr-group-label { font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.08em; color: #7A6A52; font-weight: 700; }
    .pr-field input[type=text], .pr-field input[type=number], .pr-field select, .pr-field textarea { border: 1px solid #E0D4C0; background: #fff; border-radius: 8px; padding: 9px 11px; font-size: 0.9rem; width: 100%; font-family: inherit; }
    .pr-field textarea { min-height: 96px; resize: vertical; line-height: 1.5; }
    .pr-field input:focus, .pr-field select:focus, .pr-field textarea:focus { outline: none; border-color: #8B6C4A; }
    .pr-two { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
    .pr-hint { font-size: 0.75rem; color: #7A6A52; }
    .pr-hint--warn { color: #9A4A1C; }
    .pr-photo { display: flex; gap: 12px; align-items: center; }
    .pr-photo img, .pr-photo .pr-thumb-ph { width: 72px; height: 72px; }
    .pr-upload { font-size: 0.8rem; color: #8B6C4A; font-weight: 600; cursor: pointer; }
    .pr-upload input { display: none; }
    .pr-opt { display: grid; grid-template-columns: auto minmax(0,1fr) auto auto; gap: 8px; align-items: center; background: #fff; border: 1px solid #E8DFD1; border-radius: 8px; padding: 6px 8px; }
    .pr-opt--size { grid-template-columns: minmax(0,1fr) auto auto; }
    .pr-opt img, .pr-opt .pr-thumb-ph { width: 36px; height: 36px; border-radius: 6px; cursor: pointer; }
    .pr-opt input[type=text] { border: 0; padding: 6px 4px; font-size: 0.88rem; min-width: 0; width: 100%; background: transparent; font-family: inherit; }
    .pr-opt input[type=text]:focus { outline: 1px solid #E0D4C0; border-radius: 4px; }
    .pr-stock { font-size: 0.75rem; color: #7A6A52; display: inline-flex; gap: 5px; align-items: center; white-space: nowrap; cursor: pointer; }
    .pr-x { background: none; border: 0; color: #B0A08A; cursor: pointer; font-size: 1rem; padding: 0 4px; }
    .pr-x:hover { color: #721C24; }
    .pr-add { background: none; border: 0; color: #8B6C4A; font-weight: 700; font-size: 0.8rem; cursor: pointer; padding: 0; }
    .pr-group-top { display: flex; justify-content: space-between; align-items: center; }
    .pr-group { display: flex; flex-direction: column; gap: 6px; }
    .pr-foot { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; border-top: 1px solid #E8DFD1; padding-top: 14px; }
    .pr-foot .spacer { flex: 1; }
    .pr-btn { padding: 0.55rem 1.1rem; background: #8B6C4A; color: #fff; border: none; border-radius: 8px; cursor: pointer; font-size: 0.88rem; font-weight: 600; }
    .pr-btn:hover { background: #7A5C3A; }
    .pr-btn:disabled { background: #C9B09A; cursor: not-allowed; }
    .pr-btn--ghost { background: none; color: #1E150A; border: 1px solid #E0D4C0; }
    .pr-btn--ghost:hover { background: #fff; }
    .pr-btn--danger { background: #9B2C1F; }
    .pr-btn--danger:hover { background: #7E2216; }
    .pr-del { background: none; border: 0; color: #9B2C1F; font-size: 0.82rem; cursor: pointer; padding: 0; }
    .pr-confirm { background: #F8D7DA; color: #721C24; border-radius: 8px; padding: 10px 12px; font-size: 0.85rem; display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
    .pr-msg { border-radius: 8px; padding: 9px 12px; font-size: 0.85rem; }
    .pr-msg--ok { background: #EAF3DE; color: #2E7D32; }
    .pr-msg--err { background: #FDECEA; color: #B71C1C; }
    .toolbar input[type=search] { padding: 0.45rem 0.75rem; border: 1px solid #ccc; border-radius: 6px; font-size: 0.88rem; min-width: 200px; }
    /* Website tab */
    .ws-wrap { padding: 1rem 2rem 2.5rem; display: flex; flex-direction: column; gap: 1.75rem; }
    .ws-section { background: #fff; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); padding: 1.25rem 1.5rem; display: flex; flex-direction: column; gap: 12px; min-width: 0; }
    .ws-section h3 { font-size: 1rem; color: #1E150A; }
    .ws-section > p.pr-hint { margin-top: -6px; }
    .ws-row { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
    .ws-row input[type=text] { border: 1px solid #E0D4C0; border-radius: 8px; padding: 9px 11px; font-size: 0.95rem; min-width: 220px; font-family: inherit; }
    .ws-photos { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 14px; }
    .ws-photo { border: 1px solid #E8DFD1; border-radius: 8px; overflow: hidden; display: flex; flex-direction: column; background: #FBF8F3; }
    .ws-photo img, .ws-photo .pr-thumb-ph { width: 100%; height: 140px; object-fit: cover; display: block; border-radius: 0; }
    .ws-photo-body { padding: 10px 12px; display: flex; flex-direction: column; gap: 8px; flex: 1; }
    .ws-photo-label { font-size: 0.82rem; color: #1E150A; font-weight: 600; line-height: 1.35; }
    .ws-photo-actions { display: flex; gap: 12px; align-items: center; margin-top: auto; flex-wrap: wrap; }
    .ws-tag { font-size: 0.7rem; font-weight: 700; color: #155724; background: #D4EDDA; border-radius: 999px; padding: 1px 8px; align-self: flex-start; }
    .ws-pf { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 400px); gap: 16px; align-items: start; }
    .ws-pf-rows { display: flex; flex-direction: column; gap: 2px; }
    .ws-pf-editor { background: #FBF8F3; border: 1px solid #E8DFD1; border-radius: 8px; padding: 1rem 1.25rem; display: flex; flex-direction: column; gap: 12px; min-width: 0; }
    .ws-thumb-video { width: 52px; height: 52px; object-fit: cover; border-radius: 8px; display: block; background: #EFE6D8; }
    @media (max-width: 900px) { .ws-pf { grid-template-columns: minmax(0,1fr); } .ws-wrap { padding: 1rem; } }
    @media (max-width: 900px) {
      .pr-work { grid-template-columns: minmax(0,1fr); }
      .pr-editor { border-left: 0; border-top: 1px solid #E8DFD1; }
      .pr-list { padding: 1rem; }
    }
    @media (max-width: 520px) {
      .pr-row { grid-template-columns: 44px minmax(0,1fr) auto; }
      .pr-row img, .pr-row .pr-thumb-ph { width: 44px; height: 44px; }
      .pr-price { display: none; }
      .pr-two { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>

<!-- LOGIN SCREEN -->
<div class="login-screen" id="login-screen">
  <div class="login-card">
    <div class="login-logo">moun<span>.</span></div>
    <div class="login-subtitle">Admin Dashboard</div>
    <div class="step-indicator">
      <div class="step-dot active" id="dot-1"></div>
      <div class="step-dot" id="dot-2"></div>
    </div>

    <!-- Step 1: Password -->
    <div id="step-1">
      <div class="login-step-title">Enter your password</div>
      <div class="login-step-sub">Step 1 of 2 — Password verification</div>
      <div class="login-error" id="pw-error"></div>
      <input class="login-input" type="password" id="pw-input" placeholder="Admin password" autocomplete="current-password" />
      <button class="login-btn" id="pw-btn" onclick="submitPassword()">Continue →</button>
    </div>

    <!-- Step 2: OTP -->
    <div id="step-2" style="display:none;">
      <div class="login-step-title">Check your email</div>
      <div class="login-step-sub" id="otp-hint-text">Enter the 6-digit code sent to your email.</div>
      <div class="login-error" id="otp-error"></div>
      <div class="login-success-msg" id="otp-success-msg"></div>
      <input class="login-input otp-input" type="text" id="otp-input" placeholder="000000" maxlength="6" inputmode="numeric" autocomplete="one-time-code" />
      <button class="login-btn" id="otp-btn" onclick="submitOtp()">Verify & Enter Dashboard</button>
      <div><span class="resend-link" onclick="resendOtp()">Resend code</span></div>
    </div>
  </div>
</div>

<!-- DASHBOARD -->
<div class="dashboard" id="dashboard">
  <div class="header">
    <div class="header-logo">moun. <span style="font-size:0.75rem;opacity:0.5;font-weight:400;">admin</span></div>
    <div class="header-right">
      <span class="header-sub" id="last-updated"></span>
      <button class="logout-btn" onclick="logout()">Sign out</button>
    </div>
  </div>

  <!-- Tab Navigation -->
  <div class="tab-nav">
    <button class="tab-btn active" id="tab-orders-btn" onclick="switchTab('orders')">📦 Orders</button>
    <button class="tab-btn" id="tab-quotations-btn" onclick="switchTab('quotations')">📋 Quotation Requests <span id="q-new-badge" style="display:none;background:#C9A97A;color:#fff;border-radius:10px;font-size:0.7rem;padding:1px 7px;margin-left:4px;"></span></button>
    <button class="tab-btn" id="tab-products-btn" onclick="switchTab('products')">🛍️ Products</button>
    <button class="tab-btn" id="tab-website-btn" onclick="switchTab('website')">🖼️ Website</button>
  </div>

  <!-- ORDERS TAB -->
  <div class="tab-panel active" id="tab-orders">
    <div class="toolbar">
      <select id="filter-payment">
        <option value="">All payment statuses</option>
        <option value="pending">Pending</option>
        <option value="confirmed">Confirmed</option>
        <option value="rejected">Rejected</option>
      </select>
      <select id="filter-order">
        <option value="">All order statuses</option>
        <option value="new">New</option>
        <option value="processing">Processing</option>
        <option value="shipped">Shipped</option>
        <option value="delivered">Delivered</option>
        <option value="cancelled">Cancelled</option>
      </select>
      <button onclick="loadOrders()">🔄 Refresh</button>
    </div>

    <div class="stats">
      <div class="stat-card"><div class="label">Total Orders</div><div class="value" id="stat-total">—</div></div>
      <div class="stat-card"><div class="label">Pending Payment</div><div class="value" id="stat-pending">—</div></div>
      <div class="stat-card"><div class="label">Confirmed</div><div class="value" id="stat-confirmed">—</div></div>
      <div class="stat-card"><div class="label">Revenue (Confirmed)</div><div class="value" id="stat-revenue">—</div></div>
    </div>

    <div id="error-msg" hidden></div>
    <div id="loading">Loading orders...</div>
    <div class="table-wrap" id="table-wrap" hidden>
      <table>
        <thead>
          <tr>
            <th>#</th><th>Date</th><th>Customer</th><th>Phone</th>
            <th>Method</th><th>Items</th><th>Total</th>
            <th>Payment</th><th>Order Status</th><th>Receipt</th><th>Actions</th>
          </tr>
        </thead>
        <tbody id="orders-tbody"></tbody>
      </table>
    </div>
  </div>

  <!-- QUOTATIONS TAB -->
  <div class="tab-panel" id="tab-quotations">
    <div class="toolbar">
      <select id="filter-quote-status" onchange="renderQuotationsTable(allQuotations)">
        <option value="">All statuses</option>
        <option value="new">New</option>
        <option value="pending">Pending</option>
        <option value="contacted">Contacted</option>
        <option value="closed">Closed</option>
      </select>
      <input type="text" id="search-quote" placeholder="Search name, email, service…" oninput="renderQuotationsTable(allQuotations)"
        style="padding:0.45rem 0.75rem;border:1px solid #ccc;border-radius:6px;font-size:0.88rem;min-width:220px;">
      <button onclick="loadQuotations()">🔄 Refresh</button>
    </div>

    <div class="q-stats">
      <div class="stat-card"><div class="label">Total Requests</div><div class="value" id="q-stat-total">—</div></div>
      <div class="stat-card"><div class="label">New</div><div class="value" id="q-stat-new" style="color:#0C5460">—</div></div>
      <div class="stat-card"><div class="label">Contacted</div><div class="value" id="q-stat-contacted" style="color:#004085">—</div></div>
      <div class="stat-card"><div class="label">Closed</div><div class="value" id="q-stat-closed" style="color:#155724">—</div></div>
    </div>

    <div id="q-error-msg" hidden style="color:#c0392b;padding:1rem 2rem;"></div>
    <div id="q-loading" style="text-align:center;padding:3rem;color:#888;">Loading quotations...</div>
    <div class="table-wrap" id="q-table-wrap" hidden>
      <table>
        <thead>
          <tr>
            <th>#</th><th>Date</th><th>Name</th><th>Email</th><th>Phone</th>
            <th>Service</th><th>Rooms</th><th>Budget</th><th>Timeline</th>
            <th>Status</th><th>Actions</th>
          </tr>
        </thead>
        <tbody id="quotations-tbody"></tbody>
      </table>
    </div>
  </div>

  <!-- PRODUCTS TAB -->
  <div class="tab-panel" id="tab-products">
    <div class="toolbar">
      <input type="search" id="pr-search" placeholder="Search products" aria-label="Search products">
      <select id="pr-filter-cat" aria-label="Filter by category"><option value="">All categories</option></select>
      <button type="button" onclick="loadProducts()">🔄 Refresh</button>
      <button type="button" id="pr-add-btn">+ Add product</button>
    </div>
    <div id="pr-error" hidden style="color:#c0392b;padding:1rem 2rem;"></div>
    <div class="pr-work">
      <div class="pr-list">
        <div id="pr-loading" style="text-align:center;padding:2rem;color:#888;" hidden>Loading products...</div>
        <div class="pr-rows" id="pr-rows"></div>
      </div>
      <div class="pr-editor" id="pr-editor"><p class="pr-empty">Pick a product on the left to edit it, or add a new one.</p></div>
    </div>
  </div>

  <!-- WEBSITE TAB -->
  <div class="tab-panel" id="tab-website">
    <div class="ws-wrap">
      <div id="ws-loading" style="text-align:center;padding:1rem;color:#888;" hidden>Loading website content...</div>

      <section class="ws-section">
        <h3>WhatsApp number</h3>
        <p class="pr-hint">Every WhatsApp button on the website opens a chat with this number. Include the country code.</p>
        <div class="ws-row">
          <input type="text" id="ws-wa" inputmode="tel" placeholder="+250 788 123 456" aria-label="WhatsApp number">
          <button type="button" class="pr-btn" id="ws-wa-save">Save number</button>
        </div>
        <div id="ws-wa-msg" class="pr-msg" hidden></div>
      </section>

      <section class="ws-section">
        <h3>Website photos</h3>
        <p class="pr-hint">Replace any of these photos. The change shows on the website within a minute. Product and portfolio photos are changed in their own sections.</p>
        <div id="ws-photos-msg" class="pr-msg" hidden></div>
        <div class="ws-photos" id="ws-photos"></div>
      </section>

      <section class="ws-section">
        <div class="ws-row" style="justify-content:space-between">
          <h3>Portfolio</h3>
          <button type="button" class="pr-btn" id="ws-add-btn">+ Add project</button>
        </div>
        <p class="pr-hint">Projects shown on the Portfolio page, in this order. Lower position numbers come first.</p>
        <div class="ws-pf">
          <div class="pr-rows ws-pf-rows" id="ws-pf-rows"></div>
          <div class="ws-pf-editor" id="ws-pf-editor"><p class="pr-empty">Pick a project to edit it, or add a new one.</p></div>
        </div>
      </section>
    </div>
  </div>
</div>

<!-- Modal -->
<div class="modal-overlay" id="modal-overlay">
  <div class="modal">
    <button class="modal-close" onclick="closeModal()">✕</button>
    <div id="modal-body"></div>
  </div>
</div>

<script>
  const API_BASE    = window.location.origin;
  let SESSION_TOKEN = '';
  let TEMP_TOKEN    = '';
  let allOrders     = [];
  let allQuotations = [];

  document.getElementById('pw-input').addEventListener('keydown',  e => { if (e.key === 'Enter') submitPassword(); });
  document.getElementById('otp-input').addEventListener('keydown', e => { if (e.key === 'Enter') submitOtp(); });

  async function submitPassword() {
    const pw    = document.getElementById('pw-input').value.trim();
    const btn   = document.getElementById('pw-btn');
    const errEl = document.getElementById('pw-error');
    if (!pw) { showErr(errEl, 'Please enter your password.'); return; }
    btn.disabled = true; btn.textContent = 'Sending code…'; errEl.style.display = 'none';
    try {
      const res  = await fetch(`${API_BASE}/admin/send-otp`, {
        method: 'POST', headers: {'Content-Type':'application/json'},
        body: JSON.stringify({ password: pw }),
      });
      const data = await res.json();
      if (!res.ok) { showErr(errEl, data.error || 'Incorrect password.'); btn.disabled = false; btn.textContent = 'Continue →'; return; }
      if (data.session_token) { enterDashboard(data.session_token); return; }
      TEMP_TOKEN = data.temp_token;
      document.getElementById('step-1').style.display = 'none';
      document.getElementById('step-2').style.display = 'block';
      document.getElementById('dot-1').classList.replace('active','done');
      document.getElementById('dot-2').classList.add('active');
      document.getElementById('otp-hint-text').textContent = `A 6-digit code was sent to ${data.email_hint}. It expires in 10 minutes.`;
      document.getElementById('otp-input').focus();
    } catch { showErr(errEl, 'Network error. Please try again.'); btn.disabled = false; btn.textContent = 'Continue →'; }
  }

  async function submitOtp() {
    const otp   = document.getElementById('otp-input').value.trim();
    const btn   = document.getElementById('otp-btn');
    const errEl = document.getElementById('otp-error');
    if (otp.length !== 6) { showErr(errEl, 'Please enter the full 6-digit code.'); return; }
    btn.disabled = true; btn.textContent = 'Verifying…'; errEl.style.display = 'none';
    try {
      const res  = await fetch(`${API_BASE}/admin/verify-otp`, {
        method: 'POST', headers: {'Content-Type':'application/json'},
        body: JSON.stringify({ temp_token: TEMP_TOKEN, otp }),
      });
      const data = await res.json();
      if (!res.ok) {
        showErr(errEl, data.error || 'Incorrect code.');
        btn.disabled = false; btn.textContent = 'Verify & Enter Dashboard';
        document.getElementById('otp-input').value = '';
        document.getElementById('otp-input').focus();
        return;
      }
      enterDashboard(data.session_token);
    } catch { showErr(errEl, 'Network error.'); btn.disabled = false; btn.textContent = 'Verify & Enter Dashboard'; }
  }

  function enterDashboard(token) {
    SESSION_TOKEN = token;
    document.getElementById('login-screen').style.display = 'none';
    document.getElementById('dashboard').style.display    = 'block';
    loadOrders();
    loadQuotations();
  }

  async function resendOtp() {
    const pw        = document.getElementById('pw-input').value.trim();
    const successEl = document.getElementById('otp-success-msg');
    const errEl     = document.getElementById('otp-error');
    errEl.style.display = 'none'; successEl.style.display = 'none';
    try {
      const res  = await fetch(`${API_BASE}/admin/send-otp`, {
        method: 'POST', headers: {'Content-Type':'application/json'},
        body: JSON.stringify({ password: pw }),
      });
      const data = await res.json();
      if (res.ok) {
        TEMP_TOKEN = data.temp_token;
        successEl.textContent = `New code sent to ${data.email_hint}.`;
        successEl.style.display = 'block';
        document.getElementById('otp-input').value = '';
        document.getElementById('otp-input').focus();
      } else { showErr(errEl, data.error || 'Failed to resend.'); }
    } catch { showErr(errEl, 'Network error.'); }
  }

  function logout() {
    SESSION_TOKEN = ''; TEMP_TOKEN = '';
    window.location.href = '/';
  }

  function showErr(el, msg) { el.textContent = msg; el.style.display = 'block'; }

  async function loadOrders() {
    document.getElementById('loading').hidden    = false;
    document.getElementById('table-wrap').hidden = true;
    document.getElementById('error-msg').hidden  = true;
    try {
      const res  = await fetch(`${API_BASE}/api/orders?session=${SESSION_TOKEN}`);
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Failed to load orders');
      allOrders = data.orders;
      renderTable(allOrders); renderStats(allOrders);
      document.getElementById('last-updated').textContent = 'Last updated: ' + new Date().toLocaleTimeString();
    } catch (err) {
      const errEl = document.getElementById('error-msg');
      errEl.textContent = 'Error: ' + err.message; errEl.hidden = false;
    } finally { document.getElementById('loading').hidden = true; }
  }

  function renderStats(orders) {
    const pending   = orders.filter(o => o.payment_status === 'pending').length;
    const confirmed = orders.filter(o => o.payment_status === 'confirmed').length;
    const revenue   = orders.filter(o => o.payment_status === 'confirmed').reduce((s,o) => s + o.total_amount, 0);
    document.getElementById('stat-total').textContent     = orders.length;
    document.getElementById('stat-pending').textContent   = pending;
    document.getElementById('stat-confirmed').textContent = confirmed;
    document.getElementById('stat-revenue').textContent   = 'RWF ' + revenue.toLocaleString();
  }

  function renderTable(orders) {
    const pF = document.getElementById('filter-payment').value;
    const oF = document.getElementById('filter-order').value;
    const filtered = orders.filter(o => (!pF || o.payment_status===pF) && (!oF || o.order_status===oF));
    const tbody = document.getElementById('orders-tbody');
    tbody.innerHTML = '';
    if (!filtered.length) {
      tbody.innerHTML = '<tr><td colspan="11" style="text-align:center;color:#888;padding:2rem">No orders found.</td></tr>';
      document.getElementById('table-wrap').hidden = false; return;
    }
    filtered.forEach(order => {
      const date = new Date(order.created_at).toLocaleDateString('en-GB', {day:'2-digit',month:'short',year:'numeric',hour:'2-digit',minute:'2-digit'});
      const receipt = order.receipt_url ? `<a class="receipt-link" href="${order.receipt_url}" target="_blank">View 🖼</a>` : '<span style="color:#ccc">None</span>';
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td><strong>#${order.id}</strong></td>
        <td style="white-space:nowrap">${date}</td>
        <td>${order.customer_name}</td><td>${order.phone}</td>
        <td>${order.delivery_method==='pickup'?'🏬 Pickup':'🚚 Delivery'}</td>
        <td>${order.item_count}</td>
        <td>RWF ${order.total_amount.toLocaleString()}</td>
        <td>
          <select class="status-select" data-id="${order.id}" data-type="payment">
            <option value="pending"   ${order.payment_status==='pending'  ?'selected':''}>Pending</option>
            <option value="confirmed" ${order.payment_status==='confirmed'?'selected':''}>Confirmed</option>
            <option value="rejected"  ${order.payment_status==='rejected' ?'selected':''}>Rejected</option>
          </select>
          <button class="save-btn" onclick="updateStatus(${order.id},'payment')">Save</button>
        </td>
        <td>
          <select class="status-select" data-id="${order.id}" data-type="order">
            <option value="new"        ${order.order_status==='new'       ?'selected':''}>New</option>
            <option value="processing" ${order.order_status==='processing'?'selected':''}>Processing</option>
            <option value="shipped"    ${order.order_status==='shipped'   ?'selected':''}>Shipped</option>
            <option value="delivered"  ${order.order_status==='delivered' ?'selected':''}>Delivered</option>
            <option value="cancelled"  ${order.order_status==='cancelled' ?'selected':''}>Cancelled</option>
          </select>
          <button class="save-btn" onclick="updateStatus(${order.id},'order')">Save</button>
        </td>
        <td>${receipt}</td>
        <td><button class="save-btn" onclick="viewOrder(${order.id})">Details</button></td>
      `;
      tbody.appendChild(tr);
    });
    document.getElementById('table-wrap').hidden = false;
  }

  async function updateStatus(orderId, type) {
    const select = document.querySelector(`.status-select[data-id="${orderId}"][data-type="${type}"]`);
    if (!select) return;
    const body = type==='payment' ? {payment_status:select.value} : {order_status:select.value};
    const res = await fetch(`${API_BASE}/api/orders/${orderId}?session=${SESSION_TOKEN}`, {
      method:'PUT', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body),
    });
    if (res.ok) {
      const order = allOrders.find(o => o.id===orderId);
      if (order) { if (type==='payment') order.payment_status=select.value; else order.order_status=select.value; }
      renderStats(allOrders);
      select.style.outline = '2px solid #4CAF50';
      setTimeout(() => select.style.outline='', 1500);
    } else { alert('Update failed.'); }
  }

  async function viewOrder(orderId) {
    const res  = await fetch(`${API_BASE}/api/orders/${orderId}?session=${SESSION_TOKEN}`);
    const data = await res.json();
    if (!res.ok) { alert('Could not load order.'); return; }
    const {order, items} = data;
    const date = new Date(order.created_at).toLocaleString('en-GB');
    const itemRows = items.map(i => `
      <tr>
        <td>${i.product_name}</td><td>${i.print_name||'—'}</td><td>${i.size||'—'}</td>
        <td>${i.quantity}</td><td>RWF ${i.price.toLocaleString()}</td>
        <td>RWF ${(i.price*i.quantity).toLocaleString()}</td>
      </tr>`).join('');
    const receiptSection = order.receipt_url
      ? `<p style="margin-top:1rem"><strong>Receipt:</strong> <a class="receipt-link" href="${order.receipt_url}" target="_blank">Open ↗</a></p>
         <img class="receipt-img" src="${order.receipt_url}" alt="Receipt" onerror="this.style.display='none'" />`
      : '<p style="margin-top:1rem;color:#888">No receipt uploaded.</p>';
    document.getElementById('modal-body').innerHTML = `
      <h2>Order #${order.id}</h2>
      <div class="detail-row"><strong>Date:</strong> ${date}</div>
      <div class="detail-row"><strong>Customer:</strong> ${order.customer_name}</div>
      <div class="detail-row"><strong>Phone:</strong> ${order.phone}</div>
      <div class="detail-row"><strong>Method:</strong> ${order.delivery_method==='pickup'?'🏬 Pickup':'🚚 Delivery'}</div>
      ${order.address?`<div class="detail-row"><strong>Address:</strong> ${order.address}</div>`:''}
      ${order.delivery_note?`<div class="detail-row"><strong>Note:</strong> ${order.delivery_note}</div>`:''}
      <div class="detail-row"><strong>Total:</strong> RWF ${order.total_amount.toLocaleString()}</div>
      <div class="detail-row"><strong>Payment:</strong> ${order.payment_status}</div>
      <div class="detail-row"><strong>Status:</strong> ${order.order_status}</div>
      <table class="items-table">
        <thead><tr><th>Product</th><th>Variant</th><th>Size</th><th>Qty</th><th>Unit</th><th>Subtotal</th></tr></thead>
        <tbody>${itemRows}</tbody>
      </table>
      ${receiptSection}`;
    document.getElementById('modal-overlay').classList.add('open');
  }

  function closeModal() { document.getElementById('modal-overlay').classList.remove('open'); }

  document.getElementById('filter-payment').addEventListener('change', () => renderTable(allOrders));
  document.getElementById('filter-order').addEventListener('change',   () => renderTable(allOrders));
  document.getElementById('modal-overlay').addEventListener('click', e => {
    if (e.target===document.getElementById('modal-overlay')) closeModal();
  });
  /* ── Tab switching ───────────────────────────────────────── */
  function switchTab(tab) {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
    document.getElementById('tab-' + tab + '-btn').classList.add('active');
    document.getElementById('tab-' + tab).classList.add('active');
    if (tab === 'quotations' && allQuotations.length === 0) loadQuotations();
    if (tab === 'products' && allProducts.length === 0) loadProducts();
    if (tab === 'website' && !wsLoaded) loadWebsite();
  }

  /* ── Quotations ──────────────────────────────────────────── */
  async function loadQuotations() {
    document.getElementById('q-loading').hidden    = false;
    document.getElementById('q-table-wrap').hidden = true;
    document.getElementById('q-error-msg').hidden  = true;
    try {
      const res  = await fetch(`${API_BASE}/api/quotations?session=${SESSION_TOKEN}`);
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Failed to load quotations');
      allQuotations = data.quotations;
      renderQuotationsStats(allQuotations);
      renderQuotationsTable(allQuotations);
      document.getElementById('last-updated').textContent = 'Last updated: ' + new Date().toLocaleTimeString();
    } catch (err) {
      const errEl = document.getElementById('q-error-msg');
      errEl.textContent = 'Error: ' + err.message; errEl.hidden = false;
    } finally { document.getElementById('q-loading').hidden = true; }
  }

  function renderQuotationsStats(quotations) {
    const newCount       = quotations.filter(q => q.status === 'new').length;
    const contactedCount = quotations.filter(q => q.status === 'contacted').length;
    const closedCount    = quotations.filter(q => q.status === 'closed').length;
    document.getElementById('q-stat-total').textContent     = quotations.length;
    document.getElementById('q-stat-new').textContent       = newCount;
    document.getElementById('q-stat-contacted').textContent = contactedCount;
    document.getElementById('q-stat-closed').textContent    = closedCount;
    const badge = document.getElementById('q-new-badge');
    if (newCount > 0) { badge.textContent = newCount; badge.style.display = 'inline'; }
    else { badge.style.display = 'none'; }
  }

  function renderQuotationsTable(quotations) {
    const statusF = document.getElementById('filter-quote-status').value;
    const searchQ = (document.getElementById('search-quote').value || '').toLowerCase();
    const filtered = quotations.filter(q => {
      const matchStatus = !statusF || q.status === statusF;
      const matchSearch = !searchQ ||
        (q.name||'').toLowerCase().includes(searchQ) ||
        (q.email||'').toLowerCase().includes(searchQ) ||
        (q.service||'').toLowerCase().includes(searchQ) ||
        (q.rooms||'').toLowerCase().includes(searchQ);
      return matchStatus && matchSearch;
    });
    const tbody = document.getElementById('quotations-tbody');
    tbody.innerHTML = '';
    if (!filtered.length) {
      tbody.innerHTML = '<tr><td colspan="11" style="text-align:center;color:#888;padding:2rem">No quotation requests found.</td></tr>';
      document.getElementById('q-table-wrap').hidden = false; return;
    }
    filtered.forEach(q => {
      const date = new Date(q.created_at).toLocaleDateString('en-GB', {day:'2-digit',month:'short',year:'numeric',hour:'2-digit',minute:'2-digit'});
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td><strong>#${q.id}</strong></td>
        <td style="white-space:nowrap">${date}</td>
        <td>${q.name||'—'}</td>
        <td><a href="mailto:${q.email}" style="color:#8B6C4A">${q.email||'—'}</a></td>
        <td>${q.phone||'—'}</td>
        <td>${q.service||'—'}</td>
        <td style="max-width:140px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${q.rooms||''}">${q.rooms||'—'}</td>
        <td style="white-space:nowrap">${q.budget||'—'}</td>
        <td style="white-space:nowrap">${q.timeline||'—'}</td>
        <td>
          <select class="status-select" data-qid="${q.id}" onchange="updateQuotationStatus(${q.id}, this.value)">
            <option value="new"       ${q.status==='new'       ?'selected':''}>New</option>
            <option value="pending"   ${q.status==='pending'   ?'selected':''}>Pending</option>
            <option value="contacted" ${q.status==='contacted' ?'selected':''}>Contacted</option>
            <option value="closed"    ${q.status==='closed'    ?'selected':''}>Closed</option>
          </select>
        </td>
        <td><button class="save-btn" onclick="viewQuotation(${q.id})">Details</button></td>
      `;
      tbody.appendChild(tr);
    });
    document.getElementById('q-table-wrap').hidden = false;
  }

  async function updateQuotationStatus(qid, newStatus) {
    const res = await fetch(`${API_BASE}/api/quotations/${qid}?session=${SESSION_TOKEN}`, {
      method: 'PUT', headers: {'Content-Type':'application/json'},
      body: JSON.stringify({status: newStatus}),
    });
    if (res.ok) {
      const q = allQuotations.find(x => x.id === qid);
      if (q) q.status = newStatus;
      renderQuotationsStats(allQuotations);
      const sel = document.querySelector(`.status-select[data-qid="${qid}"]`);
      if (sel) { sel.style.outline = '2px solid #4CAF50'; setTimeout(() => sel.style.outline='', 1500); }
    } else { alert('Status update failed.'); }
  }

  function viewQuotation(qid) {
    const q = allQuotations.find(x => x.id === qid);
    if (!q) return;
    const date = new Date(q.created_at).toLocaleString('en-GB');
    document.getElementById('modal-body').innerHTML = `
      <h2>Quotation Request #${q.id}</h2>
      <div class="detail-row"><strong>Date:</strong> ${date}</div>
      <div class="detail-row"><strong>Name:</strong> ${q.name||'—'}</div>
      <div class="detail-row"><strong>Email:</strong> <a href="mailto:${q.email}" style="color:#8B6C4A">${q.email||'—'}</a></div>
      <div class="detail-row"><strong>Phone:</strong> ${q.phone||'—'}</div>
      <div class="detail-row"><strong>Service:</strong> ${q.service||'—'}</div>
      <div class="detail-row"><strong>Rooms:</strong> ${q.rooms||'—'}</div>
      <div class="detail-row"><strong>Budget:</strong> ${q.budget||'—'}</div>
      <div class="detail-row"><strong>Timeline:</strong> ${q.timeline||'—'}</div>
      <div class="detail-row"><strong>Status:</strong> <span style="text-transform:capitalize">${q.status||'new'}</span></div>
      ${q.details ? `<div class="detail-row" style="align-items:flex-start"><strong>Project Details:</strong> <span style="white-space:pre-wrap">${q.details}</span></div>` : ''}
      <div style="margin-top:1.5rem;">
        <a href="mailto:${q.email}?subject=Your%20MOUN%20Interiors%20Quotation%20Request&body=Dear%20${encodeURIComponent(q.name||'')}%2C%0A%0AThank%20you%20for%20your%20quotation%20request."
          style="padding:0.45rem 1rem;background:#8B6C4A;color:#fff;border-radius:6px;text-decoration:none;font-size:0.85rem;">
          ✉️ Reply via Email
        </a>
      </div>
    `;
    document.getElementById('modal-overlay').classList.add('open');
  }
  /* ── Products ────────────────────────────────────────────── */
  let allProducts  = [];
  let prCategories = {};
  let prBadges     = [];
  let prSiteUrl    = API_BASE;
  let prSelected   = null;
  let prDraft      = null;
  let prDirty      = false;
  let prConfirmDel = false;

  function esc(v) {
    return String(v == null ? '' : v).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  }

  function prImg(path) {
    if (!path) return '';
    if (/^(https?:|data:|blob:)/.test(path)) return path;
    if (path.startsWith('/api/')) return API_BASE + path;
    if (!prSiteUrl) return '';
    return prSiteUrl + '/' + path.split('/').map(encodeURIComponent).join('/');
  }

  function prThumb(path, cls) {
    const src = prImg(path);
    return src
      ? `<img src="${esc(src)}" alt="" class="${cls || ''}" loading="lazy" onerror="this.outerHTML='<span class=&quot;pr-thumb-ph&quot;></span>'">`
      : '<span class="pr-thumb-ph"></span>';
  }

  async function prFetch(url, opts = {}) {
    opts.headers = Object.assign({}, opts.headers || {}, { 'X-Session-Token': SESSION_TOKEN });
    const res  = await fetch(API_BASE + url, opts);
    let data = {};
    try { data = await res.json(); } catch {}
    if (res.status === 401) throw new Error('Your session has ended. Sign out and sign in again.');
    if (!res.ok) throw new Error(data.error || 'Something went wrong. Please try again.');
    return data;
  }

  async function loadProducts() {
    const loading = document.getElementById('pr-loading');
    const errEl   = document.getElementById('pr-error');
    loading.hidden = false; errEl.hidden = true;
    try {
      const data = await prFetch('/api/admin/products');
      allProducts  = data.products;
      prCategories = data.categories;
      prBadges     = data.badges;
      prSiteUrl    = data.site_url || API_BASE;
      const sel = document.getElementById('pr-filter-cat');
      const cur = sel.value;
      sel.innerHTML = '<option value="">All categories</option>' +
        Object.entries(prCategories).map(([k, l]) => `<option value="${k}">${esc(l)}</option>`).join('');
      sel.value = cur;
      renderProductRows();
      if (prSelected) {
        const p = allProducts.find(x => x.id === prSelected);
        if (p && !prDirty) selectProduct(p.id, true);
      }
    } catch (err) {
      errEl.textContent = err.message; errEl.hidden = false;
    } finally { loading.hidden = true; }
  }

  function renderProductRows() {
    const q   = (document.getElementById('pr-search').value || '').toLowerCase();
    const cat = document.getElementById('pr-filter-cat').value;
    const list = allProducts.filter(p => (!cat || p.category === cat) && p.name.toLowerCase().includes(q));
    const wrap = document.getElementById('pr-rows');
    if (!list.length) {
      wrap.innerHTML = '<p class="pr-empty" style="padding:1rem">No products match. Use “+ Add product” to create one.</p>';
      return;
    }
    wrap.innerHTML = list.map(p => {
      const n = p.prints.length;
      const price = p.price != null ? 'RWF ' + Number(p.price).toLocaleString() : 'No price';
      return `<button type="button" class="pr-row ${p.id === prSelected ? 'selected' : ''}" data-id="${p.id}">
        ${prThumb(p.image)}
        <span><span class="pr-name">${esc(p.name)}</span><br>
          <span class="pr-meta">${esc(p.categoryLabel)} · ${n} ${n === 1 ? 'option' : 'options'}${p.badge ? ' · ' + esc(p.badge) : ''}</span></span>
        <span class="pr-price">${price}</span>
        <span class="pill ${p.visible ? 'pill--on' : 'pill--off'}">${p.visible ? 'On site' : 'Hidden'}</span>
      </button>`;
    }).join('');
    wrap.querySelectorAll('.pr-row').forEach(b => b.addEventListener('click', () => selectProduct(+b.dataset.id)));
  }

  function selectProduct(id, keepMsg) {
    if (prDirty && id !== prSelected && !prConfirmLeave()) return;
    const p = allProducts.find(x => x.id === id);
    if (!p) return;
    prSelected = id;
    prDraft = JSON.parse(JSON.stringify(p));
    prDirty = false; prConfirmDel = false;
    renderProductRows();
    renderEditor(keepMsg ? undefined : null);
  }

  function prConfirmLeave() {
    const box = document.getElementById('pr-msg');
    if (box && box.dataset.leave === '1') { box.dataset.leave = ''; return true; }
    prMessage('You have unsaved changes. Save them, or click the product again to discard them.', 'err');
    if (box) box.dataset.leave = '1';
    return false;
  }

  function newProduct() {
    if (prDirty && !prConfirmLeave()) return;
    prSelected = null;
    prDraft = {
      id: null, name: '', category: Object.keys(prCategories)[0] || 'accessories', badge: 'New',
      price: null, image: '', description: '', sizes: [{ value: 'Standard', available: true }],
      prints: [], visible: false, sortOrder: 0,
    };
    prDirty = true; prConfirmDel = false;
    renderProductRows();
    renderEditor(null);
    document.getElementById('pr-name').focus();
  }

  function prMessage(text, kind) {
    const box = document.getElementById('pr-msg');
    if (!box) return;
    box.className = 'pr-msg pr-msg--' + kind;
    box.textContent = text;
    box.hidden = false;
  }

  function renderEditor(msg) {
    const ed = document.getElementById('pr-editor');
    const p  = prDraft;
    if (!p) {
      ed.innerHTML = '<p class="pr-empty">Pick a product on the left to edit it, or add a new one.</p>';
      return;
    }
    const oldMsg = document.getElementById('pr-msg');
    const keep = msg === undefined && oldMsg && !oldMsg.hidden ? { cls: oldMsg.className, text: oldMsg.textContent } : null;
    const optLabel = p.category === 'candles' ? 'Scents' : 'Colours & finishes';
    ed.innerHTML = `
      <h3>${p.id ? 'Edit product' : 'New product'}</h3>
      <div id="pr-msg" class="pr-msg" hidden></div>
      <div class="pr-field"><label for="pr-name">Product name</label>
        <input type="text" id="pr-name" value="${esc(p.name)}" maxlength="255"></div>
      <div class="pr-two">
        <div class="pr-field"><label for="pr-cat">Category</label>
          <select id="pr-cat">${Object.entries(prCategories).map(([k, l]) => `<option value="${k}" ${k === p.category ? 'selected' : ''}>${esc(l)}</option>`).join('')}</select></div>
        <div class="pr-field"><label for="pr-badge">Badge</label>
          <input type="text" id="pr-badge" list="pr-badge-list" maxlength="30" placeholder="None" value="${esc(p.badge)}">
          <datalist id="pr-badge-list">${prBadges.map(b => `<option value="${esc(b)}"></option>`).join('')}</datalist></div>
      </div>
      <div class="pr-two">
        <div class="pr-field"><label for="pr-price">Price (RWF)</label>
          <input type="number" id="pr-price" min="0" step="1" placeholder="Leave empty to hide" value="${p.price == null ? '' : p.price}"></div>
        <div class="pr-field"><label for="pr-order">Position in shop</label>
          <input type="number" id="pr-order" min="1" step="1" value="${p.sortOrder || ''}" placeholder="Last"></div>
      </div>
      <span class="pr-hint">Products 1–4 by position also appear on the home page.</span>
      <div class="pr-field"><label for="pr-desc">Description</label>
        <textarea id="pr-desc">${esc(p.description)}</textarea></div>
      <div class="pr-group"><span class="pr-group-label">Main photo</span>
        <div class="pr-photo">${prThumb(p.image)}
          <div><label class="pr-upload">Upload a photo<input type="file" id="pr-main-file" accept="image/jpeg,image/png,image/webp"></label>
          <div class="pr-hint">JPG, PNG or WEBP. Large photos are resized automatically.</div></div></div></div>
      <div class="pr-group">
        <div class="pr-group-top"><span class="pr-group-label">Sizes</span><button type="button" class="pr-add" id="pr-add-size">+ Add size</button></div>
        ${p.sizes.map((s, i) => `<div class="pr-opt pr-opt--size">
          <input type="text" data-size-name="${i}" value="${esc(s.value)}" aria-label="Size name">
          <label class="pr-stock"><input type="checkbox" data-size-avail="${i}" ${s.available ? 'checked' : ''}>In stock</label>
          <button type="button" class="pr-x" data-size-del="${i}" aria-label="Remove size">✕</button></div>`).join('')}
      </div>
      <div class="pr-group">
        <div class="pr-group-top"><span class="pr-group-label">${optLabel}</span><button type="button" class="pr-add" id="pr-add-print">+ Add option</button></div>
        ${p.prints.length ? '' : '<span class="pr-hint">No options. Add one if the product comes in colours, finishes or scents.</span>'}
        ${p.prints.map((s, i) => `<div class="pr-opt">
          <label title="Change photo" style="cursor:pointer">${prThumb(s.image)}<input type="file" data-print-file="${i}" accept="image/jpeg,image/png,image/webp" hidden></label>
          <input type="text" data-print-name="${i}" value="${esc(s.name)}" aria-label="Option name">
          <label class="pr-stock"><input type="checkbox" data-print-avail="${i}" ${s.available ? 'checked' : ''}>In stock</label>
          <button type="button" class="pr-x" data-print-del="${i}" aria-label="Remove option">✕</button></div>`).join('')}
      </div>
      <label class="pr-stock" style="font-size:0.88rem;color:#1E150A"><input type="checkbox" id="pr-visible" ${p.visible ? 'checked' : ''}>Show this product on the website</label>
      ${prConfirmDel ? `<div class="pr-confirm">Delete “${esc(p.name)}” from the shop? This can’t be undone.
        <button type="button" class="pr-btn pr-btn--danger" id="pr-del-yes">Delete</button>
        <button type="button" class="pr-btn pr-btn--ghost" id="pr-del-no">Keep it</button></div>` : ''}
      <div class="pr-foot">
        ${p.id ? '<button type="button" class="pr-del" id="pr-del">Delete product</button>' : ''}
        <span class="spacer"></span>
        <button type="button" class="pr-btn pr-btn--ghost" id="pr-discard">Discard changes</button>
        <button type="button" class="pr-btn" id="pr-save">${p.id ? 'Save changes' : 'Add to shop'}</button>
      </div>`;

    if (keep) { const b = document.getElementById('pr-msg'); b.className = keep.cls; b.textContent = keep.text; b.hidden = false; }
    else if (msg) prMessage(msg.text, msg.kind);

    const dirty = () => { prDirty = true; };
    const bind = (id, fn) => { const el = document.getElementById(id); el.addEventListener('input', () => { fn(el); dirty(); }); el.addEventListener('change', () => { fn(el); dirty(); }); };
    bind('pr-name',  el => { p.name = el.value; });
    bind('pr-badge', el => { p.badge = el.value; });
    bind('pr-price', el => { p.price = el.value === '' ? null : el.value; });
    bind('pr-order', el => { p.sortOrder = el.value === '' ? 0 : +el.value; });
    bind('pr-desc',  el => { p.description = el.value; });
    document.getElementById('pr-cat').addEventListener('change', e => { p.category = e.target.value; dirty(); renderEditor(); });
    document.getElementById('pr-visible').addEventListener('change', e => { p.visible = e.target.checked; dirty(); });

    ed.querySelectorAll('[data-size-name]').forEach(el => el.addEventListener('input', () => { p.sizes[+el.dataset.sizeName].value = el.value; dirty(); }));
    ed.querySelectorAll('[data-size-avail]').forEach(el => el.addEventListener('change', () => { p.sizes[+el.dataset.sizeAvail].available = el.checked; dirty(); }));
    ed.querySelectorAll('[data-size-del]').forEach(el => el.addEventListener('click', () => { p.sizes.splice(+el.dataset.sizeDel, 1); dirty(); renderEditor(); }));
    ed.querySelectorAll('[data-print-name]').forEach(el => el.addEventListener('input', () => { p.prints[+el.dataset.printName].name = el.value; dirty(); }));
    ed.querySelectorAll('[data-print-avail]').forEach(el => el.addEventListener('change', () => { p.prints[+el.dataset.printAvail].available = el.checked; dirty(); }));
    ed.querySelectorAll('[data-print-del]').forEach(el => el.addEventListener('click', () => { p.prints.splice(+el.dataset.printDel, 1); dirty(); renderEditor(); }));
    ed.querySelectorAll('[data-print-file]').forEach(el => el.addEventListener('change', async () => {
      const url = await prUpload(el.files[0]);
      if (url) { p.prints[+el.dataset.printFile].image = url; dirty(); renderEditor({ text: 'Photo uploaded. Save to publish it.', kind: 'ok' }); }
    }));
    document.getElementById('pr-main-file').addEventListener('change', async e => {
      const url = await prUpload(e.target.files[0]);
      if (url) { p.image = url; dirty(); renderEditor({ text: 'Photo uploaded. Save to publish it.', kind: 'ok' }); }
    });
    document.getElementById('pr-add-size').addEventListener('click', () => { p.sizes.push({ value: '', available: true }); dirty(); renderEditor(); const all = ed.querySelectorAll('[data-size-name]'); all[all.length - 1].focus(); });
    document.getElementById('pr-add-print').addEventListener('click', () => { p.prints.push({ name: '', image: p.image, available: true }); dirty(); renderEditor(); const all = ed.querySelectorAll('[data-print-name]'); all[all.length - 1].focus(); });
    document.getElementById('pr-save').addEventListener('click', saveProduct);
    document.getElementById('pr-discard').addEventListener('click', () => {
      prDirty = false; prConfirmDel = false;
      if (prDraft.id) { selectProduct(prDraft.id); prMessage('Changes discarded.', 'ok'); }
      else { prDraft = null; renderEditor(null); }
    });
    const del = document.getElementById('pr-del');
    if (del) del.addEventListener('click', () => { prConfirmDel = true; renderEditor(); });
    const yes = document.getElementById('pr-del-yes'), no = document.getElementById('pr-del-no');
    if (yes) yes.addEventListener('click', deleteProduct);
    if (no)  no.addEventListener('click', () => { prConfirmDel = false; renderEditor(); });
  }

  async function prShrink(file) {
    if (!/^image\/(jpeg|png|webp)$/.test(file.type)) return file;
    try {
      const bmp = await createImageBitmap(file);
      const scale = Math.min(1, 1600 / Math.max(bmp.width, bmp.height));
      if (scale === 1 && file.size < 1.5 * 1024 * 1024) return file;
      const c = document.createElement('canvas');
      c.width = Math.round(bmp.width * scale); c.height = Math.round(bmp.height * scale);
      c.getContext('2d').drawImage(bmp, 0, 0, c.width, c.height);
      const keepAlpha = file.type !== 'image/jpeg';
      const blob = await new Promise(r => c.toBlob(r, keepAlpha ? 'image/webp' : 'image/jpeg', 0.85));
      return blob ? new File([blob], file.name, { type: blob.type }) : file;
    } catch { return file; }
  }

  async function prUpload(file) {
    if (!file) return null;
    prMessage('Uploading photo…', 'ok');
    file = await prShrink(file);
    if (file.size > 4 * 1024 * 1024) { prMessage('That photo is too large even after resizing. Choose one under 4 MB.', 'err'); return null; }
    const fd = new FormData();
    fd.append('image', file);
    try {
      const data = await prFetch('/api/admin/images', { method: 'POST', body: fd });
      return data.url;
    } catch (err) { prMessage(err.message, 'err'); return null; }
  }

  async function saveProduct() {
    const p = prDraft;
    if (!p.name.trim()) { prMessage('Give the product a name before saving.', 'err'); document.getElementById('pr-name').focus(); return; }
    const btn = document.getElementById('pr-save');
    btn.disabled = true; btn.textContent = 'Saving…';
    try {
      const isNew = !p.id;
      const body = JSON.stringify(p);
      const data = p.id
        ? await prFetch(`/api/admin/products/${p.id}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body })
        : await prFetch('/api/admin/products', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body });
      const saved = data.product;
      const i = allProducts.findIndex(x => x.id === saved.id);
      if (i >= 0) allProducts[i] = saved; else allProducts.push(saved);
      allProducts.sort((a, b) => a.sortOrder - b.sortOrder || a.id - b.id);
      prSelected = saved.id; prDraft = JSON.parse(JSON.stringify(saved)); prDirty = false;
      renderProductRows();
      const where = saved.visible ? (isNew ? 'is now on the website' : 'is updated on the website') : 'is saved but hidden from the website';
      renderEditor({ text: `Saved. “${saved.name}” ${where}.`, kind: 'ok' });
    } catch (err) {
      prMessage(err.message, 'err');
      btn.disabled = false; btn.textContent = p.id ? 'Save changes' : 'Add to shop';
    }
  }

  async function deleteProduct() {
    const p = prDraft;
    try {
      await prFetch(`/api/admin/products/${p.id}`, { method: 'DELETE' });
      allProducts = allProducts.filter(x => x.id !== p.id);
      prSelected = null; prDraft = null; prDirty = false; prConfirmDel = false;
      renderProductRows();
      renderEditor(null);
      document.getElementById('pr-editor').insertAdjacentHTML('afterbegin', `<div class="pr-msg pr-msg--ok">“${esc(p.name)}” was deleted.</div>`);
    } catch (err) { prMessage(err.message, 'err'); }
  }

  document.getElementById('pr-search').addEventListener('input', renderProductRows);
  document.getElementById('pr-filter-cat').addEventListener('change', renderProductRows);
  document.getElementById('pr-add-btn').addEventListener('click', newProduct);
  /* ── Website: WhatsApp, site photos, portfolio ───────────── */
  let wsLoaded = false;
  let wsPhotos = [];
  let wsPortfolio = [];
  let wsCategories = {};
  let wsSelected = null;
  let wsDraft = null;
  let wsConfirmDel = false;

  function wsMsg(id, text, kind) {
    const el = document.getElementById(id);
    if (!el) return;
    el.className = 'pr-msg pr-msg--' + kind;
    el.textContent = text;
    el.hidden = false;
  }

  async function wsUpload(file, msgId) {
    if (!file) return null;
    wsMsg(msgId, 'Uploading photo…', 'ok');
    file = await prShrink(file);
    if (file.size > 4 * 1024 * 1024) { wsMsg(msgId, 'That photo is too large even after resizing. Choose one under 4 MB.', 'err'); return null; }
    const fd = new FormData();
    fd.append('image', file);
    try {
      const data = await prFetch('/api/admin/images', { method: 'POST', body: fd });
      return data.url;
    } catch (err) { wsMsg(msgId, err.message, 'err'); return null; }
  }

  async function loadWebsite() {
    const loading = document.getElementById('ws-loading');
    loading.hidden = false;
    try {
      const data = await prFetch('/api/admin/site');
      wsPhotos = data.photos;
      wsPortfolio = data.portfolio;
      wsCategories = data.categories;
      document.getElementById('ws-wa').value = data.settings.whatsapp_number ? '+' + data.settings.whatsapp_number : '';
      renderWsPhotos();
      renderWsPortfolio();
      if (!wsDraft) renderWsEditor();
      wsLoaded = true;
    } catch (err) {
      wsMsg('ws-wa-msg', err.message, 'err');
    } finally { loading.hidden = true; }
  }

  async function saveWhatsApp() {
    const btn = document.getElementById('ws-wa-save');
    btn.disabled = true;
    try {
      const data = await prFetch('/api/admin/settings', {
        method: 'PUT', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ whatsapp_number: document.getElementById('ws-wa').value }),
      });
      document.getElementById('ws-wa').value = '+' + data.whatsapp_number;
      wsMsg('ws-wa-msg', `Saved. Every WhatsApp button on the website now goes to +${data.whatsapp_number}.`, 'ok');
    } catch (err) { wsMsg('ws-wa-msg', err.message, 'err'); }
    finally { btn.disabled = false; }
  }

  function renderWsPhotos() {
    const grid = document.getElementById('ws-photos');
    grid.innerHTML = wsPhotos.map((p, i) => `
      <div class="ws-photo">
        ${prThumb(p.replacement || p.path)}
        <div class="ws-photo-body">
          <span class="ws-photo-label">${esc(p.label)}</span>
          ${p.replacement ? '<span class="ws-tag">Replaced</span>' : ''}
          <div class="ws-photo-actions">
            <label class="pr-upload">Replace photo<input type="file" data-ws-photo="${i}" accept="image/jpeg,image/png,image/webp"></label>
            ${p.replacement ? `<button type="button" class="pr-del" data-ws-reset="${i}" style="color:#7A6A52">Restore original</button>` : ''}
          </div>
        </div>
      </div>`).join('');
    grid.querySelectorAll('[data-ws-photo]').forEach(el => el.addEventListener('change', async () => {
      const p = wsPhotos[+el.dataset.wsPhoto];
      const url = await wsUpload(el.files[0], 'ws-photos-msg');
      if (url) await setSitePhoto(p, url, `Replaced. The new photo is live: ${p.label}.`);
    }));
    grid.querySelectorAll('[data-ws-reset]').forEach(el => el.addEventListener('click', () => {
      const p = wsPhotos[+el.dataset.wsReset];
      setSitePhoto(p, '', `Restored the original photo: ${p.label}.`);
    }));
  }

  async function setSitePhoto(p, replacement, okText) {
    try {
      await prFetch('/api/admin/site-photos', {
        method: 'PUT', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: p.path, replacement }),
      });
      p.replacement = replacement;
      renderWsPhotos();
      wsMsg('ws-photos-msg', okText, 'ok');
    } catch (err) { wsMsg('ws-photos-msg', err.message, 'err'); }
  }

  function wsThumb(item) {
    if (item.mediaType === 'video') {
      const src = prImg(item.media);
      return src ? `<video class="ws-thumb-video" src="${esc(src)}" muted playsinline preload="metadata"></video>` : '<span class="pr-thumb-ph"></span>';
    }
    return prThumb(item.media);
  }

  function renderWsPortfolio() {
    const rows = document.getElementById('ws-pf-rows');
    if (!wsPortfolio.length) { rows.innerHTML = '<p class="pr-empty" style="padding:1rem">No projects yet. Use “+ Add project”.</p>'; return; }
    rows.innerHTML = wsPortfolio.map(it => `
      <button type="button" class="pr-row ${it.id === wsSelected ? 'selected' : ''}" data-id="${it.id}">
        ${wsThumb(it)}
        <span><span class="pr-name">${esc(it.title)}</span><br>
          <span class="pr-meta">${esc(it.categoryLabel)}${it.meta ? ' · ' + esc(it.meta) : ''}</span></span>
        <span class="pr-price">#${it.sortOrder}</span>
        <span class="pill ${it.visible ? 'pill--on' : 'pill--off'}">${it.visible ? 'On site' : 'Hidden'}</span>
      </button>`).join('');
    rows.querySelectorAll('.pr-row').forEach(b => b.addEventListener('click', () => {
      const it = wsPortfolio.find(x => x.id === +b.dataset.id);
      wsSelected = it.id; wsDraft = JSON.parse(JSON.stringify(it)); wsConfirmDel = false;
      renderWsPortfolio(); renderWsEditor();
    }));
  }

  function newPortfolioItem() {
    wsSelected = null; wsConfirmDel = false;
    wsDraft = { id: null, title: '', category: Object.keys(wsCategories)[0] || 'living', meta: '', media: '', mediaType: 'image', visible: true, sortOrder: 0 };
    renderWsPortfolio(); renderWsEditor();
    document.getElementById('ws-title').focus();
  }

  function renderWsEditor(msg) {
    const ed = document.getElementById('ws-pf-editor');
    const p = wsDraft;
    if (!p) { ed.innerHTML = '<p class="pr-empty">Pick a project to edit it, or add a new one.</p>'; return; }
    ed.innerHTML = `
      <h3 style="font-size:1rem;color:#1E150A">${p.id ? 'Edit project' : 'New project'}</h3>
      <div id="ws-pf-msg" class="pr-msg" hidden></div>
      <div class="pr-field"><label for="ws-title">Project title</label><input type="text" id="ws-title" maxlength="255" value="${esc(p.title)}" placeholder="e.g. Bright Family Living Room"></div>
      <div class="pr-two">
        <div class="pr-field"><label for="ws-cat">Category</label>
          <select id="ws-cat">${Object.entries(wsCategories).map(([k, l]) => `<option value="${k}" ${k === p.category ? 'selected' : ''}>${esc(l)}</option>`).join('')}</select></div>
        <div class="pr-field"><label for="ws-order">Position</label><input type="number" id="ws-order" min="1" step="1" value="${p.sortOrder || ''}" placeholder="Last"></div>
      </div>
      <div class="pr-field"><label for="ws-meta">Location and year</label><input type="text" id="ws-meta" maxlength="255" value="${esc(p.meta)}" placeholder="e.g. Remera, Kigali · 2026"></div>
      <div class="pr-group"><span class="pr-group-label">Photo</span>
        <div class="pr-photo">${wsThumb(p)}
          <div><label class="pr-upload">${p.media ? 'Change photo' : 'Upload a photo'}<input type="file" id="ws-file" accept="image/jpeg,image/png,image/webp"></label>
          <div class="pr-hint">${p.mediaType === 'video' ? 'This project shows a video. Uploading a photo replaces it.' : 'JPG, PNG or WEBP. Large photos are resized automatically.'}</div></div></div></div>
      <label class="pr-stock" style="font-size:0.88rem;color:#1E150A"><input type="checkbox" id="ws-visible" ${p.visible ? 'checked' : ''}>Show this project on the website</label>
      ${wsConfirmDel ? `<div class="pr-confirm">Delete “${esc(p.title)}” from the portfolio? This can’t be undone.
        <button type="button" class="pr-btn pr-btn--danger" id="ws-del-yes">Delete</button>
        <button type="button" class="pr-btn pr-btn--ghost" id="ws-del-no">Keep it</button></div>` : ''}
      <div class="pr-foot">
        ${p.id ? '<button type="button" class="pr-del" id="ws-del">Delete project</button>' : ''}
        <span class="spacer"></span>
        <button type="button" class="pr-btn" id="ws-save">${p.id ? 'Save changes' : 'Add to portfolio'}</button>
      </div>`;
    if (msg) wsMsg('ws-pf-msg', msg.text, msg.kind);
    const bind = (id, fn) => { const el = document.getElementById(id); el.addEventListener('input', () => fn(el)); el.addEventListener('change', () => fn(el)); };
    bind('ws-title', el => { p.title = el.value; });
    bind('ws-cat',   el => { p.category = el.value; });
    bind('ws-meta',  el => { p.meta = el.value; });
    bind('ws-order', el => { p.sortOrder = el.value === '' ? 0 : +el.value; });
    document.getElementById('ws-visible').addEventListener('change', e => { p.visible = e.target.checked; });
    document.getElementById('ws-file').addEventListener('change', async e => {
      const url = await wsUpload(e.target.files[0], 'ws-pf-msg');
      if (url) { p.media = url; p.mediaType = 'image'; renderWsEditor({ text: 'Photo uploaded. Save to publish it.', kind: 'ok' }); }
    });
    document.getElementById('ws-save').addEventListener('click', savePortfolioItem);
    const del = document.getElementById('ws-del');
    if (del) del.addEventListener('click', () => { wsConfirmDel = true; renderWsEditor(); });
    const yes = document.getElementById('ws-del-yes'), no = document.getElementById('ws-del-no');
    if (yes) yes.addEventListener('click', deletePortfolioItem);
    if (no) no.addEventListener('click', () => { wsConfirmDel = false; renderWsEditor(); });
  }

  async function savePortfolioItem() {
    const p = wsDraft;
    if (!p.title.trim()) { wsMsg('ws-pf-msg', 'Give the project a title before saving.', 'err'); return; }
    if (!p.media) { wsMsg('ws-pf-msg', 'Upload a photo before saving.', 'err'); return; }
    const isNew = !p.id;
    const btn = document.getElementById('ws-save');
    btn.disabled = true; btn.textContent = 'Saving…';
    try {
      const body = JSON.stringify(p);
      const data = isNew
        ? await prFetch('/api/admin/portfolio', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body })
        : await prFetch(`/api/admin/portfolio/${p.id}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body });
      const saved = data.item;
      const i = wsPortfolio.findIndex(x => x.id === saved.id);
      if (i >= 0) wsPortfolio[i] = saved; else wsPortfolio.push(saved);
      wsPortfolio.sort((a, b) => a.sortOrder - b.sortOrder || a.id - b.id);
      wsSelected = saved.id; wsDraft = JSON.parse(JSON.stringify(saved));
      renderWsPortfolio();
      const where = saved.visible ? (isNew ? 'is now in the portfolio' : 'is updated on the website') : 'is saved but hidden from the website';
      renderWsEditor({ text: `Saved. “${saved.title}” ${where}.`, kind: 'ok' });
    } catch (err) {
      wsMsg('ws-pf-msg', err.message, 'err');
      btn.disabled = false; btn.textContent = isNew ? 'Add to portfolio' : 'Save changes';
    }
  }

  async function deletePortfolioItem() {
    const p = wsDraft;
    try {
      await prFetch(`/api/admin/portfolio/${p.id}`, { method: 'DELETE' });
      wsPortfolio = wsPortfolio.filter(x => x.id !== p.id);
      wsSelected = null; wsDraft = null; wsConfirmDel = false;
      renderWsPortfolio(); renderWsEditor();
      document.getElementById('ws-pf-editor').insertAdjacentHTML('afterbegin', `<div class="pr-msg pr-msg--ok">“${esc(p.title)}” was deleted.</div>`);
    } catch (err) { wsMsg('ws-pf-msg', err.message, 'err'); }
  }

  document.getElementById('ws-wa-save').addEventListener('click', saveWhatsApp);
  document.getElementById('ws-add-btn').addEventListener('click', newPortfolioItem);
</script>
</body>
</html>
"""

@app.route('/admin')
def admin():
    """Admin dashboard with email OTP 2FA."""
    return Response(ADMIN_HTML, mimetype='text/html')


# ── Run ───────────────────────────────────────────────────────

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
