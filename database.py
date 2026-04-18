"""
database.py - SQLite3 Database Layer for Mobile Shop Management System
Handles all DB operations: migrations, CRUD for inventory, maintenance, wallets, accounting.
"""

import sqlite3
import os
import uuid
import hashlib
from datetime import datetime, date
from contextlib import contextmanager

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mobile_shop.db")


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def generate_id() -> str:
    return uuid.uuid4().hex[:12].upper()


def generate_sku() -> str:
    return f"SKU-{uuid.uuid4().hex[:8].upper()}"


def generate_transaction_id() -> str:
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"TXN-{ts}-{uuid.uuid4().hex[:4].upper()}"


@contextmanager
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Migration / Schema
# ---------------------------------------------------------------------------

SCHEMA_VERSION = 1

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('admin', 'staff')),
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS inventory (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    code TEXT UNIQUE,
    barcode TEXT UNIQUE,
    category TEXT DEFAULT '',
    buy_price REAL NOT NULL DEFAULT 0,
    sell_price REAL NOT NULL DEFAULT 0,
    quantity INTEGER NOT NULL DEFAULT 0,
    low_stock_threshold INTEGER NOT NULL DEFAULT 5,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS maintenance (
    id TEXT PRIMARY KEY,
    customer_name TEXT NOT NULL,
    phone TEXT DEFAULT '',
    device_type TEXT NOT NULL,
    issue_description TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'received'
        CHECK(status IN ('received', 'in_progress', 'ready', 'delivered')),
    spare_part_cost REAL NOT NULL DEFAULT 0,
    service_fee REAL NOT NULL DEFAULT 0,
    spare_part_inventory_id TEXT DEFAULT NULL,
    notes TEXT DEFAULT '',
    received_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    delivered_at TEXT DEFAULT NULL,
    FOREIGN KEY (spare_part_inventory_id) REFERENCES inventory(id)
);

CREATE TABLE IF NOT EXISTS wallets (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    provider TEXT NOT NULL,
    phone_number TEXT DEFAULT '',
    monthly_limit REAL NOT NULL DEFAULT 200000,
    balance REAL NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS wallet_transactions (
    id TEXT PRIMARY KEY,
    wallet_id TEXT NOT NULL,
    transaction_type TEXT NOT NULL CHECK(transaction_type IN ('deposit', 'withdraw', 'transfer')),
    amount REAL NOT NULL,
    client_phone TEXT DEFAULT '',
    system_fee REAL NOT NULL DEFAULT 0,
    shop_commission REAL NOT NULL DEFAULT 0,
    notes TEXT DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (wallet_id) REFERENCES wallets(id)
);

CREATE TABLE IF NOT EXISTS vaults (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    vault_type TEXT NOT NULL CHECK(vault_type IN ('cash', 'bank', 'digital')),
    balance REAL NOT NULL DEFAULT 0,
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS transactions (
    id TEXT PRIMARY KEY,
    vault_id TEXT NOT NULL,
    source_type TEXT NOT NULL
        CHECK(source_type IN ('sale', 'repair', 'wallet_commission', 'transfer_in', 'transfer_out', 'adjustment')),
    source_id TEXT DEFAULT '',
    amount REAL NOT NULL,
    description TEXT DEFAULT '',
    shift_date TEXT NOT NULL DEFAULT (date('now')),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (vault_id) REFERENCES vaults(id)
);

CREATE TABLE IF NOT EXISTS sales (
    id TEXT PRIMARY KEY,
    inventory_id TEXT NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 1,
    unit_sell_price REAL NOT NULL,
    unit_buy_price REAL NOT NULL,
    total REAL NOT NULL,
    profit REAL NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (inventory_id) REFERENCES inventory(id)
);
"""


def init_db():
    """Initialize database with schema and seed data."""
    with get_connection() as conn:
        conn.executescript(SCHEMA_SQL)

        # Check version
        cur = conn.execute("SELECT version FROM schema_version ORDER BY version DESC LIMIT 1")
        row = cur.fetchone()
        if row is None:
            conn.execute("INSERT INTO schema_version (version) VALUES (?)", (SCHEMA_VERSION,))

        # Seed default admin if no users exist
        cur = conn.execute("SELECT COUNT(*) as cnt FROM users")
        if cur.fetchone()["cnt"] == 0:
            conn.execute(
                "INSERT INTO users (id, username, password_hash, role) VALUES (?, ?, ?, ?)",
                (generate_id(), "admin", _hash_password("Muhamed@3512139M"), "admin"),
            )

        # Seed default vaults if none exist
        cur = conn.execute("SELECT COUNT(*) as cnt FROM vaults")
        if cur.fetchone()["cnt"] == 0:
            for name, vtype in [
                ("الخزنة النقدية", "cash"),
                ("البنك / إنستاباي", "bank"),
                ("المحافظ الرقمية", "digital"),
            ]:
                conn.execute(
                    "INSERT INTO vaults (id, name, vault_type, balance) VALUES (?, ?, ?, 0)",
                    (generate_id(), name, vtype),
                )


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

def authenticate(username: str, password: str):
    with get_connection() as conn:
        cur = conn.execute(
            "SELECT * FROM users WHERE username = ? AND password_hash = ?",
            (username, _hash_password(password)),
        )
        return cur.fetchone()


def get_all_users():
    with get_connection() as conn:
        return conn.execute("SELECT id, username, role, created_at FROM users").fetchall()


def add_user(username: str, password: str, role: str):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO users (id, username, password_hash, role) VALUES (?, ?, ?, ?)",
            (generate_id(), username, _hash_password(password), role),
        )


def delete_user(user_id: str):
    with get_connection() as conn:
        conn.execute("DELETE FROM users WHERE id = ?", (user_id,))


# ---------------------------------------------------------------------------
# Inventory
# ---------------------------------------------------------------------------

def get_all_inventory():
    with get_connection() as conn:
        return conn.execute("SELECT * FROM inventory ORDER BY updated_at DESC").fetchall()


def search_inventory(query: str):
    with get_connection() as conn:
        q = f"%{query}%"
        return conn.execute(
            "SELECT * FROM inventory WHERE name LIKE ? OR code LIKE ? OR barcode LIKE ? ORDER BY name",
            (q, q, q),
        ).fetchall()


def get_inventory_item(item_id: str):
    with get_connection() as conn:
        return conn.execute("SELECT * FROM inventory WHERE id = ?", (item_id,)).fetchone()


def add_inventory_item(name, code, barcode, category, buy_price, sell_price, quantity, low_stock_threshold):
    item_id = generate_id()
    if not code:
        code = generate_sku()
    if not barcode:
        barcode = f"BC-{uuid.uuid4().hex[:10].upper()}"
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO inventory
               (id, name, code, barcode, category, buy_price, sell_price, quantity, low_stock_threshold)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (item_id, name, code, barcode, category, buy_price, sell_price, quantity, low_stock_threshold),
        )
    return item_id


def update_inventory_item(item_id, name, code, barcode, category, buy_price, sell_price, quantity, low_stock_threshold):
    with get_connection() as conn:
        conn.execute(
            """UPDATE inventory SET name=?, code=?, barcode=?, category=?, buy_price=?, sell_price=?,
               quantity=?, low_stock_threshold=?, updated_at=datetime('now') WHERE id=?""",
            (name, code, barcode, category, buy_price, sell_price, quantity, low_stock_threshold, item_id),
        )


def delete_inventory_item(item_id):
    with get_connection() as conn:
        conn.execute("DELETE FROM inventory WHERE id = ?", (item_id,))


def deduct_stock(item_id: str, qty: int):
    with get_connection() as conn:
        conn.execute(
            "UPDATE inventory SET quantity = quantity - ?, updated_at = datetime('now') WHERE id = ? AND quantity >= ?",
            (qty, item_id, qty),
        )
        return conn.execute("SELECT changes()").fetchone()[0] > 0


def get_low_stock_items():
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM inventory WHERE quantity <= low_stock_threshold ORDER BY quantity ASC"
        ).fetchall()


def quick_update_price(item_id: str, new_sell_price: float):
    with get_connection() as conn:
        conn.execute(
            "UPDATE inventory SET sell_price = ?, updated_at = datetime('now') WHERE id = ?",
            (new_sell_price, item_id),
        )


# ---------------------------------------------------------------------------
# Sales
# ---------------------------------------------------------------------------

def record_sale(inventory_id, quantity, unit_sell_price, unit_buy_price, vault_id):
    sale_id = generate_id()
    total = quantity * unit_sell_price
    profit = quantity * (unit_sell_price - unit_buy_price)
    txn_id = generate_transaction_id()

    with get_connection() as conn:
        # Deduct stock
        conn.execute(
            "UPDATE inventory SET quantity = quantity - ?, updated_at = datetime('now') WHERE id = ? AND quantity >= ?",
            (quantity, inventory_id, quantity),
        )
        if conn.execute("SELECT changes()").fetchone()[0] == 0:
            raise ValueError("المخزون غير كافٍ")

        conn.execute(
            "INSERT INTO sales (id, inventory_id, quantity, unit_sell_price, unit_buy_price, total, profit) VALUES (?,?,?,?,?,?,?)",
            (sale_id, inventory_id, quantity, unit_sell_price, unit_buy_price, total, profit),
        )

        # Record in vault
        conn.execute(
            "INSERT INTO transactions (id, vault_id, source_type, source_id, amount, description, shift_date) VALUES (?,?,?,?,?,?,?)",
            (txn_id, vault_id, "sale", sale_id, total, f"بيع اكسسوار - ربح: {profit:.2f}", date.today().isoformat()),
        )
        conn.execute(
            "UPDATE vaults SET balance = balance + ?, updated_at = datetime('now') WHERE id = ?",
            (total, vault_id),
        )

    return sale_id, profit


def get_sales(from_date=None, to_date=None):
    with get_connection() as conn:
        sql = """SELECT s.*, i.name as item_name FROM sales s
                 JOIN inventory i ON s.inventory_id = i.id"""
        params = []
        if from_date and to_date:
            sql += " WHERE date(s.created_at) BETWEEN ? AND ?"
            params = [from_date, to_date]
        sql += " ORDER BY s.created_at DESC"
        return conn.execute(sql, params).fetchall()


# ---------------------------------------------------------------------------
# Maintenance
# ---------------------------------------------------------------------------

def get_all_maintenance():
    with get_connection() as conn:
        return conn.execute("SELECT * FROM maintenance ORDER BY received_at DESC").fetchall()


def get_maintenance_by_status(status: str):
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM maintenance WHERE status = ? ORDER BY received_at DESC", (status,)
        ).fetchall()


def add_maintenance(customer_name, phone, device_type, issue_description, spare_part_cost, service_fee,
                    spare_part_inventory_id, notes):
    m_id = generate_id()
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO maintenance
               (id, customer_name, phone, device_type, issue_description, spare_part_cost, service_fee,
                spare_part_inventory_id, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (m_id, customer_name, phone, device_type, issue_description,
             spare_part_cost, service_fee, spare_part_inventory_id, notes),
        )
        # Deduct spare part from inventory if linked
        if spare_part_inventory_id:
            conn.execute(
                "UPDATE inventory SET quantity = quantity - 1, updated_at = datetime('now') WHERE id = ? AND quantity >= 1",
                (spare_part_inventory_id,),
            )
    return m_id


def update_maintenance_status(m_id: str, new_status: str, vault_id: str = None):
    with get_connection() as conn:
        now = datetime.now().isoformat()
        updates = "status = ?, updated_at = ?"
        params = [new_status, now]

        if new_status == "delivered":
            updates += ", delivered_at = ?"
            params.append(now)

        params.append(m_id)
        conn.execute(f"UPDATE maintenance SET {updates} WHERE id = ?", params)

        # When delivered, record profit in vault
        if new_status == "delivered" and vault_id:
            row = conn.execute("SELECT * FROM maintenance WHERE id = ?", (m_id,)).fetchone()
            if row:
                net_profit = row["service_fee"] - row["spare_part_cost"]
                total = row["service_fee"]
                txn_id = generate_transaction_id()
                conn.execute(
                    "INSERT INTO transactions (id, vault_id, source_type, source_id, amount, description, shift_date) VALUES (?,?,?,?,?,?,?)",
                    (txn_id, vault_id, "repair", m_id, total,
                     f"صيانة - {row['device_type']} - ربح صافي: {net_profit:.2f}",
                     date.today().isoformat()),
                )
                conn.execute(
                    "UPDATE vaults SET balance = balance + ?, updated_at = datetime('now') WHERE id = ?",
                    (total, vault_id),
                )


def update_maintenance(m_id, customer_name, phone, device_type, issue_description,
                       spare_part_cost, service_fee, notes):
    with get_connection() as conn:
        conn.execute(
            """UPDATE maintenance SET customer_name=?, phone=?, device_type=?, issue_description=?,
               spare_part_cost=?, service_fee=?, notes=?, updated_at=datetime('now') WHERE id=?""",
            (customer_name, phone, device_type, issue_description, spare_part_cost, service_fee, notes, m_id),
        )


def delete_maintenance(m_id: str):
    with get_connection() as conn:
        conn.execute("DELETE FROM maintenance WHERE id = ?", (m_id,))


def search_maintenance(query: str):
    with get_connection() as conn:
        q = f"%{query}%"
        return conn.execute(
            """SELECT * FROM maintenance WHERE customer_name LIKE ? OR phone LIKE ?
               OR device_type LIKE ? ORDER BY received_at DESC""",
            (q, q, q),
        ).fetchall()


# ---------------------------------------------------------------------------
# Wallets
# ---------------------------------------------------------------------------

def get_all_wallets():
    with get_connection() as conn:
        return conn.execute("SELECT * FROM wallets ORDER BY created_at DESC").fetchall()


def add_wallet(name, provider, phone_number, monthly_limit, balance=0):
    w_id = generate_id()
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO wallets (id, name, provider, phone_number, monthly_limit, balance) VALUES (?,?,?,?,?,?)",
            (w_id, name, provider, phone_number, monthly_limit, balance),
        )
    return w_id


def update_wallet(w_id, name, provider, phone_number, monthly_limit):
    with get_connection() as conn:
        conn.execute(
            "UPDATE wallets SET name=?, provider=?, phone_number=?, monthly_limit=? WHERE id=?",
            (name, provider, phone_number, monthly_limit, w_id),
        )


def delete_wallet(w_id: str):
    with get_connection() as conn:
        conn.execute("DELETE FROM wallet_transactions WHERE wallet_id = ?", (w_id,))
        conn.execute("DELETE FROM wallets WHERE id = ?", (w_id,))


def get_wallet_monthly_usage(wallet_id: str):
    """Get total transaction amount for the current month."""
    with get_connection() as conn:
        first_of_month = date.today().replace(day=1).isoformat()
        cur = conn.execute(
            """SELECT COALESCE(SUM(amount), 0) as total FROM wallet_transactions
               WHERE wallet_id = ? AND date(created_at) >= ?""",
            (wallet_id, first_of_month),
        )
        return cur.fetchone()["total"]


def add_wallet_transaction(wallet_id, transaction_type, amount, client_phone, system_fee, shop_commission, notes,
                           vault_id=None):
    t_id = generate_id()
    txn_id = generate_transaction_id()

    with get_connection() as conn:
        conn.execute(
            """INSERT INTO wallet_transactions
               (id, wallet_id, transaction_type, amount, client_phone, system_fee, shop_commission, notes)
               VALUES (?,?,?,?,?,?,?,?)""",
            (t_id, wallet_id, transaction_type, amount, client_phone, system_fee, shop_commission, notes),
        )

        # Update wallet balance
        if transaction_type == "deposit":
            conn.execute("UPDATE wallets SET balance = balance + ? WHERE id = ?", (amount, wallet_id))
        elif transaction_type == "withdraw":
            conn.execute("UPDATE wallets SET balance = balance - ? WHERE id = ?", (amount, wallet_id))

        # Record commission in vault
        if vault_id and shop_commission > 0:
            conn.execute(
                "INSERT INTO transactions (id, vault_id, source_type, source_id, amount, description, shift_date) VALUES (?,?,?,?,?,?,?)",
                (txn_id, vault_id, "wallet_commission", t_id, shop_commission,
                 f"عمولة محفظة - {amount:.2f} ج.م", date.today().isoformat()),
            )
            conn.execute(
                "UPDATE vaults SET balance = balance + ?, updated_at = datetime('now') WHERE id = ?",
                (shop_commission, vault_id),
            )

    return t_id


def get_wallet_transactions(wallet_id=None, from_date=None, to_date=None):
    with get_connection() as conn:
        sql = """SELECT wt.*, w.name as wallet_name FROM wallet_transactions wt
                 JOIN wallets w ON wt.wallet_id = w.id WHERE 1=1"""
        params = []
        if wallet_id:
            sql += " AND wt.wallet_id = ?"
            params.append(wallet_id)
        if from_date and to_date:
            sql += " AND date(wt.created_at) BETWEEN ? AND ?"
            params.extend([from_date, to_date])
        sql += " ORDER BY wt.created_at DESC"
        return conn.execute(sql, params).fetchall()


# ---------------------------------------------------------------------------
# Vaults & Accounting
# ---------------------------------------------------------------------------

def get_all_vaults():
    with get_connection() as conn:
        return conn.execute("SELECT * FROM vaults ORDER BY vault_type").fetchall()


def get_vault_by_type(vault_type: str):
    with get_connection() as conn:
        return conn.execute("SELECT * FROM vaults WHERE vault_type = ?", (vault_type,)).fetchone()


def transfer_between_vaults(from_vault_id, to_vault_id, amount, description=""):
    txn_out = generate_transaction_id()
    txn_in = generate_transaction_id()
    with get_connection() as conn:
        conn.execute(
            "UPDATE vaults SET balance = balance - ?, updated_at = datetime('now') WHERE id = ?",
            (amount, from_vault_id),
        )
        conn.execute(
            "UPDATE vaults SET balance = balance + ?, updated_at = datetime('now') WHERE id = ?",
            (amount, to_vault_id),
        )
        conn.execute(
            "INSERT INTO transactions (id, vault_id, source_type, source_id, amount, description, shift_date) VALUES (?,?,?,?,?,?,?)",
            (txn_out, from_vault_id, "transfer_out", to_vault_id, -amount,
             description or "تحويل بين الخزائن", date.today().isoformat()),
        )
        conn.execute(
            "INSERT INTO transactions (id, vault_id, source_type, source_id, amount, description, shift_date) VALUES (?,?,?,?,?,?,?)",
            (txn_in, to_vault_id, "transfer_in", from_vault_id, amount,
             description or "تحويل بين الخزائن", date.today().isoformat()),
        )


def adjust_vault(vault_id, amount, description=""):
    txn_id = generate_transaction_id()
    with get_connection() as conn:
        conn.execute(
            "UPDATE vaults SET balance = balance + ?, updated_at = datetime('now') WHERE id = ?",
            (amount, vault_id),
        )
        conn.execute(
            "INSERT INTO transactions (id, vault_id, source_type, source_id, amount, description, shift_date) VALUES (?,?,?,?,?,?,?)",
            (txn_id, vault_id, "adjustment", "", amount,
             description or "تعديل يدوي", date.today().isoformat()),
        )


def get_transactions(vault_id=None, from_date=None, to_date=None, source_type=None):
    with get_connection() as conn:
        sql = """SELECT t.*, v.name as vault_name FROM transactions t
                 JOIN vaults v ON t.vault_id = v.id WHERE 1=1"""
        params = []
        if vault_id:
            sql += " AND t.vault_id = ?"
            params.append(vault_id)
        if from_date and to_date:
            sql += " AND t.shift_date BETWEEN ? AND ?"
            params.extend([from_date, to_date])
        if source_type:
            sql += " AND t.source_type = ?"
            params.append(source_type)
        sql += " ORDER BY t.created_at DESC"
        return conn.execute(sql, params).fetchall()


def get_profit_summary(from_date=None, to_date=None):
    """Return dict with accessory_profit, maintenance_profit, wallet_commissions."""
    with get_connection() as conn:
        sales_filter = ""
        maint_filter = ""
        wallet_filter = ""
        params_sales = []
        params_maint = []
        params_wallet = []
        if from_date and to_date:
            sales_filter = " AND date(created_at) BETWEEN ? AND ?"
            params_sales = [from_date, to_date]
            maint_filter = " AND date(received_at) BETWEEN ? AND ?"
            params_maint = [from_date, to_date]
            wallet_filter = " AND date(created_at) BETWEEN ? AND ?"
            params_wallet = [from_date, to_date]

        # Accessories profit
        cur = conn.execute(
            f"SELECT COALESCE(SUM(profit), 0) as total FROM sales WHERE 1=1{sales_filter}", params_sales
        )
        acc_profit = cur.fetchone()["total"]

        # Maintenance profit
        cur = conn.execute(
            f"SELECT COALESCE(SUM(service_fee - spare_part_cost), 0) as total FROM maintenance WHERE status='delivered'{maint_filter}",
            params_maint,
        )
        maint_profit = cur.fetchone()["total"]

        # Wallet commissions
        cur = conn.execute(
            f"SELECT COALESCE(SUM(shop_commission), 0) as total FROM wallet_transactions WHERE 1=1{wallet_filter}",
            params_wallet,
        )
        wallet_comm = cur.fetchone()["total"]

        return {
            "accessory_profit": acc_profit,
            "maintenance_profit": maint_profit,
            "wallet_commissions": wallet_comm,
            "total": acc_profit + maint_profit + wallet_comm,
        }


def get_daily_summary(target_date=None):
    if target_date is None:
        target_date = date.today().isoformat()
    with get_connection() as conn:
        cur = conn.execute(
            "SELECT source_type, SUM(amount) as total FROM transactions WHERE shift_date = ? GROUP BY source_type",
            (target_date,),
        )
        return {row["source_type"]: row["total"] for row in cur.fetchall()}
