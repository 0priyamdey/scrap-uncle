"""
Migrate data from local SQLite (scrap.db) to the production PostgreSQL database.

Usage:
    1. Set DATABASE_URL in your .env to point to your Supabase / Railway / Neon DB.
    2. Run init_db.py first to create the schema:  python init_db.py
    3. Run this script:  python migrate_sqlite_to_pg.py

This script reads all rows from the local scrap.db and inserts them into
the PostgreSQL database specified by DATABASE_URL.
"""

import os
import sqlite3
import sys

from dotenv import load_dotenv

load_dotenv()


def get_sqlite_connection():
    """Connect to the local SQLite database."""
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scrap.db")
    if not os.path.exists(db_path):
        print("ERROR: scrap.db not found. Nothing to migrate.")
        sys.exit(1)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def migrate():
    """Transfer all data from SQLite to PostgreSQL."""
    database_url = os.environ.get("DATABASE_URL", "")
    if not database_url:
        print("ERROR: DATABASE_URL is not set. Cannot migrate to PostgreSQL.")
        print("       Set DATABASE_URL in your .env file and try again.")
        sys.exit(1)

    # Import production db module (which will connect to PostgreSQL)
    from db import db

    if not db.is_postgres:
        print("ERROR: DATABASE_URL does not point to a PostgreSQL database.")
        sys.exit(1)

    sqlite_conn = get_sqlite_connection()
    cursor = sqlite_conn.cursor()

    # ── 1. Migrate users ──────────────────────────────────────
    print("Migrating users...")
    users = cursor.execute("SELECT id, name, phone, email, hash FROM users").fetchall()
    for user in users:
        try:
            db.execute(
                "INSERT INTO users (id, name, phone, email, hash) VALUES (?, ?, ?, ?, ?) RETURNING id",
                user["id"], user["name"], user["phone"], user["email"], user["hash"]
            )
        except Exception as e:
            print(f"  [WARN] Skipping user {user['name']} (id={user['id']}): {e}")
    print(f"  [OK] {len(users)} users processed.")

    # ── 2. Migrate user_addresses ─────────────────────────────
    print("Migrating user addresses...")
    addresses = cursor.execute(
        "SELECT aid, id, state, city, address, pincode FROM user_addresses"
    ).fetchall()
    for addr in addresses:
        try:
            db.execute(
                "INSERT INTO user_addresses (aid, id, state, city, address, pincode) VALUES (?, ?, ?, ?, ?, ?) RETURNING aid",
                addr["aid"], addr["id"], addr["state"], addr["city"],
                addr["address"], addr["pincode"]
            )
        except Exception as e:
            print(f"  [WARN] Skipping address aid={addr['aid']}: {e}")
    print(f"  [OK] {len(addresses)} addresses processed.")

    # ── 3. Migrate orders ─────────────────────────────────────
    print("Migrating orders...")
    orders = cursor.execute(
        "SELECT order_id, user_id, pickup_date, time_slot, vehicle_type, "
        "estimated_weight, status, created_at, aid FROM orders"
    ).fetchall()
    for order in orders:
        try:
            db.execute(
                "INSERT INTO orders (order_id, user_id, pickup_date, time_slot, "
                "vehicle_type, estimated_weight, status, created_at, aid) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?) RETURNING order_id",
                order["order_id"], order["user_id"], order["pickup_date"],
                order["time_slot"], order["vehicle_type"], order["estimated_weight"],
                order["status"], order["created_at"], order["aid"]
            )
        except Exception as e:
            print(f"  [WARN] Skipping order {order['order_id']}: {e}")
    print(f"  [OK] {len(orders)} orders processed.")

    # ── 4. Migrate order_items ────────────────────────────────
    print("Migrating order items...")
    items = cursor.execute(
        "SELECT item_id, order_id, category, rate_per_kg, weight_collected, "
        "total_amount, setteled_date FROM order_items"
    ).fetchall()
    for item in items:
        try:
            db.execute(
                "INSERT INTO order_items (item_id, order_id, category, rate_per_kg, "
                "weight_collected, total_amount, setteled_date) "
                "VALUES (?, ?, ?, ?, ?, ?, ?) RETURNING item_id",
                item["item_id"], item["order_id"], item["category"],
                item["rate_per_kg"], item["weight_collected"],
                item["total_amount"], item["setteled_date"]
            )
        except Exception as e:
            print(f"  [WARN] Skipping order_item {item['item_id']}: {e}")
    print(f"  [OK] {len(items)} order items processed.")

    # ── 5. Migrate admin_creds ────────────────────────────────
    print("Migrating admin credentials...")
    admins = cursor.execute(
        "SELECT admin_id, name, hash FROM admin_creds"
    ).fetchall()
    for admin in admins:
        try:
            db.execute(
                "INSERT INTO admin_creds (admin_id, name, hash) VALUES (?, ?, ?) RETURNING admin_id",
                admin["admin_id"], admin["name"], admin["hash"]
            )
        except Exception as e:
            print(f"  [WARN] Skipping admin {admin['name']}: {e}")
    print(f"  [OK] {len(admins)} admin accounts processed.")

    # ── 6. Reset sequences to avoid ID conflicts ──────────────
    print("Resetting PostgreSQL sequences...")
    sequence_resets = [
        "SELECT setval('users_id_seq', COALESCE((SELECT MAX(id) FROM users), 0))",
        "SELECT setval('user_addresses_aid_seq', COALESCE((SELECT MAX(aid) FROM user_addresses), 0))",
        "SELECT setval('orders_order_id_seq', COALESCE((SELECT MAX(order_id) FROM orders), 0))",
        "SELECT setval('order_items_item_id_seq', COALESCE((SELECT MAX(item_id) FROM order_items), 0))",
        "SELECT setval('admin_creds_admin_id_seq', COALESCE((SELECT MAX(admin_id) FROM admin_creds), 0))",
    ]
    for sql in sequence_resets:
        try:
            db.execute(sql)
        except Exception as e:
            print(f"  [WARN] Sequence reset warning: {e}")
    print("  [OK] Sequences reset.")

    sqlite_conn.close()
    print()
    print("Migration complete!")


if __name__ == "__main__":
    print("=" * 50)
    print("  Scrap Uncle -- SQLite to PostgreSQL Migration")
    print("=" * 50)
    print()
    migrate()
