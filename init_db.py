"""
Initialize the database schema and seed the default admin account.

Usage:
    python init_db.py

Reads DATABASE_URL from .env (or environment variables).
If DATABASE_URL is empty, falls back to local SQLite (scrap.db).
"""

import os
import sys

from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

load_dotenv()

# Import the shared database singleton
from db import db


def init_db():
    """Create all tables from schema.sql."""
    schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema.sql")

    if not os.path.exists(schema_path):
        print("ERROR: schema.sql not found.")
        sys.exit(1)

    with open(schema_path, "r") as f:
        schema_sql = f.read()

    if db.is_postgres:
        # PostgreSQL: execute the entire schema as one block
        from sqlalchemy import text
        engine = db._get_engine()
        with engine.connect() as conn:
            conn.execute(text(schema_sql))
            conn.commit()
        print("[OK] PostgreSQL schema created successfully.")
    else:
        # SQLite: execute statement by statement (can't run multi-statement text())
        import sqlite3
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scrap.db")
        conn = sqlite3.connect(db_path)
        # Convert PostgreSQL-specific syntax to SQLite-compatible syntax
        sqlite_schema = schema_sql
        sqlite_schema = sqlite_schema.replace("SERIAL PRIMARY KEY", "INTEGER PRIMARY KEY AUTOINCREMENT")
        sqlite_schema = sqlite_schema.replace("BIGINT", "INTEGER")
        sqlite_schema = sqlite_schema.replace("TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP",
                                               "TEXT DEFAULT (datetime('now', 'localtime'))")
        conn.executescript(sqlite_schema)
        conn.close()
        print("[OK] SQLite schema created successfully (scrap.db).")


def seed_admin():
    """Create the default admin account if none exists."""
    existing = db.execute("SELECT COUNT(*) AS cnt FROM admin_creds")
    count = existing[0]["cnt"] if existing else 0

    if count > 0:
        print("[INFO] Admin account already exists -- skipping seed.")
        return

    admin_user = os.environ.get("ADMIN_USER", "admin")
    admin_password = os.environ.get("ADMIN_PASSWORD", "admin123")
    hashed = generate_password_hash(admin_password)

    if db.is_postgres:
        db.execute(
            "INSERT INTO admin_creds (name, hash) VALUES (?, ?) RETURNING admin_id",
            admin_user, hashed
        )
    else:
        db.execute(
            "INSERT INTO admin_creds (name, hash) VALUES (?, ?)",
            admin_user, hashed
        )

    print(f"[OK] Admin account created -- user: {admin_user}")


if __name__ == "__main__":
    print("=" * 50)
    print("  Scrap Uncle -- Database Initialization")
    print("=" * 50)

    db_url = os.environ.get("DATABASE_URL", "")
    if db_url:
        print(f"  Target: PostgreSQL ({db_url[:40]}...)")
    else:
        print("  Target: Local SQLite (scrap.db)")

    print()
    init_db()
    seed_admin()
    print()
    print("Done! Your database is ready.")
