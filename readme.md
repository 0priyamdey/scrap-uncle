# 🗑️ ScrapUncle

A scrap collection and recycling management platform built with **Flask** (Python). Users can schedule scrap pickups, track orders, and view earnings analytics. Admins can manage all orders and users from a dedicated dashboard.

Originally built as a CS50 Final Project — now production-ready with **PostgreSQL** (Supabase / Railway / Neon) support.

---

## ✨ Features

- **User Dashboard** — View earnings, weight recycled, carbon offset, and active pickup requests.
- **Order Management** — Place pickup orders with category selection, date/time scheduling, and address selection.
- **Profile Management** — Update name, email, password, and manage multiple addresses.
- **Admin Panel** — View all orders in a table, edit status, category, rates, weights, and settlement info via modal.
- **Analytics Charts** — Doughnut and bar charts (Chart.js) showing scrap composition and earnings breakdown.

---

## 🛠️ Tech Stack

| Layer        | Technology                     |
| ------------ | ------------------------------ |
| Backend      | Flask (Python 3.12+)           |
| Frontend     | Jinja2 Templates + Bootstrap 5 |
| Database     | PostgreSQL (Supabase/Railway)  |
| DB Driver    | SQLAlchemy + psycopg2-binary   |
| WSGI Server  | Gunicorn                       |
| Charts       | Chart.js                       |

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- A PostgreSQL database (free options: [Supabase](https://supabase.com), [Railway](https://railway.app), [Neon](https://neon.tech), [Render](https://render.com))

### 1. Clone & Install

```bash
git clone https://github.com/YOUR_USERNAME/scrap-uncle.git
cd scrap-uncle
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and set:
- `DATABASE_URL` — Your PostgreSQL connection string (leave empty for local SQLite)
- `SECRET_KEY` — A random secret for session signing
- `ADMIN_USER` / `ADMIN_PASSWORD` — Initial admin credentials

### 3. Initialize the Database

```bash
python init_db.py
```

This creates all tables and seeds the default admin account.

### 4. (Optional) Migrate Existing SQLite Data

If you have existing data in `scrap.db` that you want to move to PostgreSQL:

```bash
python migrate_sqlite_to_pg.py
```

### 5. Run Locally

```bash
# Development (with auto-reload)
python app.py

# Production (Linux/Mac)
gunicorn app:app --bind 0.0.0.0:5000
```

Visit: `http://localhost:5000`

---

## ☁️ Deployment

### Railway

1. Push your code to GitHub.
2. Create a new project on [Railway](https://railway.app).
3. Add a **PostgreSQL** plugin to get a `DATABASE_URL`.
4. Set environment variables (`SECRET_KEY`, `ADMIN_USER`, `ADMIN_PASSWORD`).
5. Deploy — Railway auto-detects the `Procfile`.
6. Run `python init_db.py` from the Railway shell to set up tables.

### Render

1. Push to GitHub.
2. Create a new **Web Service** on [Render](https://render.com).
3. Add a **PostgreSQL** database.
4. Set the Build Command: `pip install -r requirements.txt`
5. Set the Start Command: `gunicorn app:app`
6. Add environment variables and deploy.

### Supabase (Database Only)

1. Create a project on [Supabase](https://supabase.com).
2. Go to **Settings → Database → Connection string** → copy the URI.
3. Paste it as `DATABASE_URL` in your `.env` or deployment platform.
4. Deploy your Flask app on Railway / Render / any VPS.

---

## 📁 Project Structure

```
scrap-uncle/
├── app.py                  # Flask application (routes)
├── db.py                   # Database abstraction layer (SQLAlchemy)
├── helpers.py              # Auth decorators (login_required, admin_required)
├── schema.sql              # PostgreSQL table definitions
├── init_db.py              # Database initialization + admin seeding
├── migrate_sqlite_to_pg.py # SQLite → PostgreSQL migration tool
├── requirements.txt        # Python dependencies
├── Procfile                # Railway / Render process declaration
├── vercel.json             # Vercel deployment config
├── .env.example            # Environment variable template
├── .gitignore
├── static/
│   ├── styles.css
│   └── js/
│       ├── dashboard.js    # Chart.js analytics
│       └── update.js       # Admin modal JS
└── templates/
    ├── layout.html         # User layout (navbar + flash messages)
    ├── adminlayout.html    # Admin layout
    ├── index.html          # User dashboard
    ├── login.html          # User login
    ├── register.html       # User registration
    ├── orders.html         # User orders (live + past)
    ├── placeorder.html     # Place new order form
    ├── profile.html        # User profile & addresses
    ├── contacts.html       # Contact information
    ├── admin.html          # Admin order management
    ├── adminlogin.html     # Admin login
    └── users.html          # Admin user list
```

---

## 📄 License

MIT
# scrap-uncle
