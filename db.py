"""
Database abstraction layer for Scrap Uncle.

Replaces the cs50.SQL wrapper with a production-grade SQLAlchemy engine.
Supports PostgreSQL (Supabase, Railway, Neon, Render) via DATABASE_URL,
and falls back to local SQLite for offline development.

Usage:
    from db import db
    rows = db.execute("SELECT * FROM users WHERE id = %s", user_id)
"""

import os
import re
import sqlite3
import urllib.parse

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL, make_url
from sqlalchemy.pool import QueuePool

load_dotenv()


def parse_database_url(url_str: str):
    """
    Robustly parse database URLs, handling:
    - Accidental quotes or 'DATABASE_URL=' prefix
    - Unencoded or encoded special characters in passwords (e.g. '@', '%40')
    - postgres:// -> postgresql:// alias
    """
    url_str = url_str.strip().strip("\"'").strip()
    if url_str.startswith("DATABASE_URL="):
        url_str = url_str[len("DATABASE_URL="):].strip().strip("\"'").strip()

    if not url_str or url_str.startswith("sqlite:"):
        return url_str

    # Extract components: postgresql://[user]:[password]@[host]:[port]/[database]
    pattern = r"^(?:postgresql|postgres)(?:\+[a-zA-Z0-9_]+)?:\/\/([^:]+):(.*)@([^:\/\?]+)(?::(\d+))?(?:\/([^?]*))?(?:\?(.*))?$"
    match = re.match(pattern, url_str)
    if match:
        user, raw_pwd, host, port, db_name, query_params = match.groups()
        clean_pwd = urllib.parse.unquote(raw_pwd)
        return URL.create(
            drivername="postgresql+psycopg2",
            username=user,
            password=clean_pwd,
            host=host,
            port=int(port) if port else 5432,
            database=db_name if db_name else "postgres",
        )

    if url_str.startswith("postgres://"):
        url_str = url_str.replace("postgres://", "postgresql://", 1)

    return make_url(url_str)


class Database:
    """Thin wrapper around SQLAlchemy that mimics the cs50.SQL interface."""

    def __init__(self):
        self._engine = None
        self._is_postgres = False

    def _get_engine(self):
        """Lazy-initialize the database engine on first use."""
        if self._engine is not None:
            return self._engine

        raw_url = os.environ.get("DATABASE_URL", "").strip()
        is_serverless = bool(os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"))

        parsed_url = parse_database_url(raw_url) if raw_url else ""

        if not parsed_url:
            if is_serverless:
                raise RuntimeError(
                    "DATABASE_URL environment variable is missing on Vercel! "
                    "Please add DATABASE_URL in Vercel Project Settings -> Environment Variables, "
                    "then Redeploy the latest deployment."
                )

            # Fallback to local SQLite for offline development only
            db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scrap.db")
            url = f"sqlite:///{db_path}"
            self._is_postgres = False
            self._engine = create_engine(
                url,
                connect_args={"check_same_thread": False},
                pool_pre_ping=True,
            )
            # Enable WAL mode and foreign keys for SQLite
            from sqlalchemy import event

            @event.listens_for(self._engine, "connect")
            def _set_sqlite_pragma(dbapi_conn, connection_record):
                if isinstance(dbapi_conn, sqlite3.Connection):
                    cursor = dbapi_conn.cursor()
                    cursor.execute("PRAGMA journal_mode=WAL")
                    cursor.execute("PRAGMA foreign_keys=ON")
                    cursor.close()
        else:
            self._is_postgres = True

            if is_serverless:
                from sqlalchemy.pool import NullPool
                self._engine = create_engine(
                    parsed_url,
                    poolclass=NullPool,
                    pool_pre_ping=True,
                )
            else:
                self._engine = create_engine(
                    parsed_url,
                    poolclass=QueuePool,
                    pool_size=5,
                    max_overflow=10,
                    pool_pre_ping=True,
                    pool_recycle=300,
                )

        return self._engine

    @property
    def is_postgres(self):
        """Check if the active database is PostgreSQL."""
        self._get_engine()
        return self._is_postgres

    def execute(self, sql, *args):
        """
        Execute a SQL statement and return results.

        For SELECT queries, returns a list of dicts.
        For INSERT with RETURNING, returns the value of the first column
        of the first row (typically the auto-generated ID).
        For UPDATE/DELETE, returns the number of affected rows.
        """
        engine = self._get_engine()

        # Convert ? placeholders to :p0, :p1, ... for SQLAlchemy
        param_index = [0]

        def _replace_placeholder(match):
            idx = param_index[0]
            param_index[0] += 1
            return f":p{idx}"

        converted_sql = re.sub(r"\?", _replace_placeholder, sql)

        # Build the named parameter dict
        params = {f"p{i}": v for i, v in enumerate(args)}

        # Determine query type
        stripped = sql.strip().upper()
        is_select = stripped.startswith("SELECT")
        is_insert = stripped.startswith("INSERT")
        is_returning = "RETURNING" in stripped

        with engine.connect() as conn:
            result = conn.execute(text(converted_sql), params)

            if is_select:
                columns = result.keys()
                rows = [dict(zip(columns, row)) for row in result.fetchall()]
                conn.commit()
                return rows
            elif is_insert and is_returning:
                row = result.fetchone()
                conn.commit()
                return row[0] if row else None
            elif is_insert and not self._is_postgres:
                # SQLite: return lastrowid for INSERT without RETURNING
                lastrowid = result.lastrowid
                conn.commit()
                return lastrowid
            else:
                rowcount = result.rowcount
                conn.commit()
                return rowcount


# Singleton instance — import this in app.py
db = Database()
