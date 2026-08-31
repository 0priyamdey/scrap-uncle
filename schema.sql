-- =============================================================
-- Scrap Uncle — Production PostgreSQL Schema
-- =============================================================
-- Run this file against your Supabase / Railway / Neon database
-- to create all required tables.
--
-- Usage:
--   python init_db.py          (recommended — also seeds admin)
--   psql $DATABASE_URL < schema.sql  (manual, tables only)
-- =============================================================

-- Users
CREATE TABLE IF NOT EXISTS users (
    id          SERIAL PRIMARY KEY,
    name        TEXT    NOT NULL,
    phone       BIGINT  UNIQUE NOT NULL,
    email       TEXT    UNIQUE,
    hash        TEXT    NOT NULL
);

-- User addresses (one user → many addresses)
CREATE TABLE IF NOT EXISTS user_addresses (
    aid         SERIAL  PRIMARY KEY,
    id          INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    state       TEXT    NOT NULL,
    city        TEXT    NOT NULL,
    address     TEXT    NOT NULL,
    pincode     INTEGER NOT NULL
);

-- Orders
CREATE TABLE IF NOT EXISTS orders (
    order_id        SERIAL  PRIMARY KEY,
    user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    pickup_date     TEXT    NOT NULL,
    time_slot       TEXT    NOT NULL,
    vehicle_type    TEXT    NOT NULL,
    estimated_weight TEXT,
    status          TEXT    DEFAULT 'Pending',
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    aid             INTEGER NOT NULL REFERENCES user_addresses(aid) ON DELETE CASCADE
);

-- Order items (one order → one item row for now)
CREATE TABLE IF NOT EXISTS order_items (
    item_id         SERIAL  PRIMARY KEY,
    order_id        INTEGER NOT NULL REFERENCES orders(order_id) ON DELETE CASCADE,
    category        TEXT    NOT NULL,
    rate_per_kg     REAL,
    weight_collected REAL,
    total_amount    REAL,
    setteled_date   TEXT
);

-- Admin credentials
CREATE TABLE IF NOT EXISTS admin_creds (
    admin_id    SERIAL PRIMARY KEY,
    name        TEXT   UNIQUE NOT NULL,
    hash        TEXT   NOT NULL
);

-- ======================== Indexes ========================
CREATE INDEX IF NOT EXISTS idx_orders_user_id   ON orders(user_id);
CREATE INDEX IF NOT EXISTS idx_orders_status    ON orders(status);
CREATE INDEX IF NOT EXISTS idx_order_items_oid  ON order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_user_addr_uid    ON user_addresses(id);
