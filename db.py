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

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.pool import QueuePool

load_dotenv()


class Database:
    """Thin wrapper around SQLAlchemy that mimics the cs50.SQL interface."""

    def __init__(self):
        self._engine = None
        self._is_postgres = False

    def _get_engine(self):
        """Lazy-initialize the database engine on first use."""
        if self._engine is not None:
            return self._engine

        url = os.environ.get("DATABASE_URL", "")

        if not url:
            # Fallback to local SQLite for offline development
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
            # Railway / Heroku sometimes provide postgres:// instead of postgresql://
            if url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql://", 1)
            self._is_postgres = True
            self._engine = create_engine(
                url,
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

        Parameters use :param style for SQLAlchemy text() binding.
        The method accepts positional args matching ? placeholders in the SQL,
        which are automatically converted to named :p0, :p1, ... placeholders.
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
