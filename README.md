# MOUN — Interior Design & Home Décor

Website, shop and admin dashboard for MOUN, Kigali. Everything runs as one Vercel project:

- `public/` — the website (HTML, CSS, JS, photos), served as static files
- `index.py` + `backend/` — the Flask backend (orders, quotation requests, admin dashboard, products), run by Vercel as a Python function
- Database: Neon PostgreSQL

## Admin dashboard

Open `/admin` on the site (or click the admin icon in the header). Sign in with the admin password, then the 6-digit code emailed to the admin address.

Tabs:
- **Orders** and **Quotation requests** — as before
- **Products** — add, edit, hide and delete products; set prices (RWF); upload photos; mark sizes and colours/scents as sold out. Changes show on the website straight away.

The first time the backend runs, it copies the 8 original products into the database. After that, the dashboard is where products are managed. If the backend is ever unreachable, the website shows the built-in product list instead of an empty shop.

## Deploy on Vercel

1. Put this folder in a GitHub repository (or replace the contents of the existing one).
2. In Vercel, import the repository (or open the existing project). Framework preset: **Flask** (Vercel usually detects it). Leave build settings empty.
3. In **Settings → Environment Variables**, add the values from `backend/.env.example`:
   - `DATABASE_URL` — use the existing Neon connection string to keep all current orders and quotations
   - `ADMIN_PASSWORD`, `SECRET_KEY`
   - `SMTP_EMAIL`, `SMTP_PASSWORD` (Gmail App Password), `ADMIN_EMAIL`
   - Optional: `FIREBASE_CREDENTIALS`, `FIREBASE_STORAGE_BUCKET` for payment receipt uploads
4. Deploy. Then open `/admin`, sign in, and check the Products tab.

## Run locally

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp backend/.env.example backend/.env    # fill it in
npm i -g vercel && vercel dev           # website + backend at http://localhost:3000
```

© 2026 MOUN — Kigali, Rwanda
