"""
Maestro ERP - Database Manager
Handles all SQLite database operations with Foreign Keys enabled.
Auto-generates the database schema on startup.
"""

import sqlite3
import os
import json
from datetime import datetime, date


DB_PATH = "maestro_erp.db"


def get_connection():
    """Get a database connection with foreign keys enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database():
    """Create all tables if they don't exist."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS levels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        );

        CREATE TABLE IF NOT EXISTS teachers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT,
            subject TEXT
        );

        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            level_id INTEGER,
            teacher_id INTEGER,
            monthly_price REAL DEFAULT 0,
            FOREIGN KEY (level_id) REFERENCES levels(id) ON DELETE SET NULL,
            FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS course_schedules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER NOT NULL,
            day TEXT NOT NULL,
            time TEXT NOT NULL,
            FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS groups_ (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            course_id INTEGER NOT NULL,
            selected_days_json TEXT DEFAULT '[]',
            FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT,
            group_id INTEGER,
            status TEXT DEFAULT 'active',
            FOREIGN KEY (group_id) REFERENCES groups_(id) ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            group_id INTEGER,
            total_required REAL DEFAULT 0,
            paid_amount REAL DEFAULT 0,
            due_date TEXT,
            created_at TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
            FOREIGN KEY (group_id) REFERENCES groups_(id) ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS finance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL CHECK(type IN ('income', 'expense')),
            category TEXT,
            amount REAL NOT NULL,
            date TEXT DEFAULT (date('now','localtime')),
            notes TEXT,
            student_id INTEGER,
            FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS student_ledger (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            description TEXT,
            debit REAL DEFAULT 0,
            credit REAL DEFAULT 0,
            balance REAL DEFAULT 0,
            date TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            group_id INTEGER,
            date TEXT DEFAULT (date('now','localtime')),
            status TEXT DEFAULT 'present' CHECK(status IN ('present', 'absent', 'charged_absence')),
            FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
            FOREIGN KEY (group_id) REFERENCES groups_(id) ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT NOT NULL,
            stock INTEGER DEFAULT 0,
            price REAL DEFAULT 0
        );
    """)

    conn.commit()
    conn.close()


# ======================== LEVELS ========================

def add_level(name):
    conn = get_connection()
    try:
        conn.execute("INSERT INTO levels (name) VALUES (?)", (name,))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def get_all_levels():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM levels ORDER BY id").fetchall()
    conn.close()
    return rows


def update_level(level_id, name):
    conn = get_connection()
    conn.execute("UPDATE levels SET name=? WHERE id=?", (name, level_id))
    conn.commit()
    conn.close()


def delete_level(level_id):
    conn = get_connection()
    conn.execute("DELETE FROM levels WHERE id=?", (level_id,))
    conn.commit()
    conn.close()


# ======================== TEACHERS ========================

def add_teacher(name, phone, subject):
    conn = get_connection()
    conn.execute("INSERT INTO teachers (name, phone, subject) VALUES (?, ?, ?)",
                 (name, phone, subject))
    conn.commit()
    conn.close()


def get_all_teachers():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM teachers ORDER BY id").fetchall()
    conn.close()
    return rows


def update_teacher(teacher_id, name, phone, subject):
    conn = get_connection()
    conn.execute("UPDATE teachers SET name=?, phone=?, subject=? WHERE id=?",
                 (name, phone, subject, teacher_id))
    conn.commit()
    conn.close()


def delete_teacher(teacher_id):
    conn = get_connection()
    conn.execute("DELETE FROM teachers WHERE id=?", (teacher_id,))
    conn.commit()
    conn.close()


# ======================== COURSES ========================

def add_course(name, level_id, teacher_id, monthly_price):
    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO courses (name, level_id, teacher_id, monthly_price) VALUES (?, ?, ?, ?)",
        (name, level_id, teacher_id, monthly_price))
    course_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return course_id


def get_all_courses():
    conn = get_connection()
    rows = conn.execute("""
        SELECT c.*, l.name as level_name, t.name as teacher_name
        FROM courses c
        LEFT JOIN levels l ON c.level_id = l.id
        LEFT JOIN teachers t ON c.teacher_id = t.id
        ORDER BY c.id
    """).fetchall()
    conn.close()
    return rows


def update_course(course_id, name, level_id, teacher_id, monthly_price):
    conn = get_connection()
    conn.execute(
        "UPDATE courses SET name=?, level_id=?, teacher_id=?, monthly_price=? WHERE id=?",
        (name, level_id, teacher_id, monthly_price, course_id))
    conn.commit()
    conn.close()


def delete_course(course_id):
    conn = get_connection()
    conn.execute("DELETE FROM courses WHERE id=?", (course_id,))
    conn.commit()
    conn.close()


def get_course_by_id(course_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM courses WHERE id=?", (course_id,)).fetchone()
    conn.close()
    return row


# ======================== COURSE SCHEDULES ========================

def add_course_schedule(course_id, day, time_str):
    conn = get_connection()
    conn.execute("INSERT INTO course_schedules (course_id, day, time) VALUES (?, ?, ?)",
                 (course_id, day, time_str))
    conn.commit()
    conn.close()


def get_course_schedules(course_id):
    conn = get_connection()
    rows = conn.execute("SELECT * FROM course_schedules WHERE course_id=? ORDER BY id",
                        (course_id,)).fetchall()
    conn.close()
    return rows


def delete_course_schedule(schedule_id):
    conn = get_connection()
    conn.execute("DELETE FROM course_schedules WHERE id=?", (schedule_id,))
    conn.commit()
    conn.close()


def clear_course_schedules(course_id):
    conn = get_connection()
    conn.execute("DELETE FROM course_schedules WHERE course_id=?", (course_id,))
    conn.commit()
    conn.close()


# ======================== GROUPS ========================

def add_group(name, course_id, selected_days_json):
    conn = get_connection()
    conn.execute("INSERT INTO groups_ (name, course_id, selected_days_json) VALUES (?, ?, ?)",
                 (name, course_id, selected_days_json))
    conn.commit()
    conn.close()


def get_all_groups():
    conn = get_connection()
    rows = conn.execute("""
        SELECT g.*, c.name as course_name, c.monthly_price
        FROM groups_ g
        LEFT JOIN courses c ON g.course_id = c.id
        ORDER BY g.id
    """).fetchall()
    conn.close()
    return rows


def get_group_by_id(group_id):
    conn = get_connection()
    row = conn.execute("""
        SELECT g.*, c.name as course_name, c.monthly_price
        FROM groups_ g
        LEFT JOIN courses c ON g.course_id = c.id
        WHERE g.id=?
    """, (group_id,)).fetchone()
    conn.close()
    return row


def update_group(group_id, name, course_id, selected_days_json):
    conn = get_connection()
    conn.execute("UPDATE groups_ SET name=?, course_id=?, selected_days_json=? WHERE id=?",
                 (name, course_id, selected_days_json, group_id))
    conn.commit()
    conn.close()


def delete_group(group_id):
    conn = get_connection()
    conn.execute("DELETE FROM groups_ WHERE id=?", (group_id,))
    conn.commit()
    conn.close()


def get_groups_for_today(today_day_name):
    """Get groups that have a schedule for today."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT g.*, c.name as course_name
        FROM groups_ g
        LEFT JOIN courses c ON g.course_id = c.id
        ORDER BY g.id
    """).fetchall()
    conn.close()
    result = []
    for row in rows:
        try:
            days = json.loads(row['selected_days_json'])
            if today_day_name in days:
                result.append(row)
        except (json.JSONDecodeError, TypeError):
            pass
    return result


# ======================== STUDENTS ========================

def add_student(name, phone, group_id):
    conn = get_connection()
    cursor = conn.execute("INSERT INTO students (name, phone, group_id) VALUES (?, ?, ?)",
                          (name, phone, group_id))
    student_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return student_id


def get_all_students():
    conn = get_connection()
    rows = conn.execute("""
        SELECT s.id, s.name, s.phone, s.group_id, s.status,
               g.name as group_name,
               COALESCE(sub.total_required, 0) as total_required,
               COALESCE(sub.paid_amount, 0) as paid_amount,
               (COALESCE(sub.total_required, 0) - COALESCE(sub.paid_amount, 0)) as debt,
               sub.due_date,
               (SELECT a.date FROM attendance a WHERE a.student_id = s.id ORDER BY a.date DESC LIMIT 1) as last_attendance
        FROM students s
        LEFT JOIN groups_ g ON s.group_id = g.id
        LEFT JOIN subscriptions sub ON sub.student_id = s.id AND sub.id = (
            SELECT sub2.id FROM subscriptions sub2 WHERE sub2.student_id = s.id ORDER BY sub2.id DESC LIMIT 1
        )
        ORDER BY s.id
    """).fetchall()
    conn.close()
    return rows


def get_student_by_id(student_id):
    conn = get_connection()
    row = conn.execute("""
        SELECT s.*, g.name as group_name
        FROM students s
        LEFT JOIN groups_ g ON s.group_id = g.id
        WHERE s.id=?
    """, (student_id,)).fetchone()
    conn.close()
    return row


def update_student(student_id, name, phone, group_id, status):
    conn = get_connection()
    conn.execute("UPDATE students SET name=?, phone=?, group_id=?, status=? WHERE id=?",
                 (name, phone, group_id, status, student_id))
    conn.commit()
    conn.close()


def delete_student(student_id):
    conn = get_connection()
    conn.execute("DELETE FROM students WHERE id=?", (student_id,))
    conn.commit()
    conn.close()


def search_students(query):
    conn = get_connection()
    rows = conn.execute("""
        SELECT s.id, s.name, s.phone, s.group_id, s.status,
               g.name as group_name,
               COALESCE(sub.total_required, 0) as total_required,
               COALESCE(sub.paid_amount, 0) as paid_amount,
               (COALESCE(sub.total_required, 0) - COALESCE(sub.paid_amount, 0)) as debt,
               sub.due_date,
               (SELECT a.date FROM attendance a WHERE a.student_id = s.id ORDER BY a.date DESC LIMIT 1) as last_attendance
        FROM students s
        LEFT JOIN groups_ g ON s.group_id = g.id
        LEFT JOIN subscriptions sub ON sub.student_id = s.id AND sub.id = (
            SELECT sub2.id FROM subscriptions sub2 WHERE sub2.student_id = s.id ORDER BY sub2.id DESC LIMIT 1
        )
        WHERE s.name LIKE ? OR s.phone LIKE ?
        ORDER BY s.id
    """, (f"%{query}%", f"%{query}%")).fetchall()
    conn.close()
    return rows


def transfer_students_to_group(student_ids, new_group_id):
    conn = get_connection()
    for sid in student_ids:
        conn.execute("UPDATE students SET group_id=? WHERE id=?", (new_group_id, sid))
    conn.commit()
    conn.close()


def delete_students_bulk(student_ids):
    conn = get_connection()
    for sid in student_ids:
        conn.execute("DELETE FROM students WHERE id=?", (sid,))
    conn.commit()
    conn.close()


def get_students_by_group(group_id):
    conn = get_connection()
    rows = conn.execute("""
        SELECT s.* FROM students s WHERE s.group_id=? AND s.status='active' ORDER BY s.name
    """, (group_id,)).fetchall()
    conn.close()
    return rows


# ======================== SUBSCRIPTIONS ========================

def add_subscription(student_id, group_id, total_required, paid_amount, due_date):
    conn = get_connection()
    conn.execute(
        "INSERT INTO subscriptions (student_id, group_id, total_required, paid_amount, due_date) VALUES (?, ?, ?, ?, ?)",
        (student_id, group_id, total_required, paid_amount, due_date))
    conn.commit()
    conn.close()


def get_student_subscriptions(student_id):
    conn = get_connection()
    rows = conn.execute("""
        SELECT sub.*, g.name as group_name
        FROM subscriptions sub
        LEFT JOIN groups_ g ON sub.group_id = g.id
        WHERE sub.student_id=?
        ORDER BY sub.id DESC
    """, (student_id,)).fetchall()
    conn.close()
    return rows


def get_latest_subscription(student_id):
    conn = get_connection()
    row = conn.execute("""
        SELECT * FROM subscriptions WHERE student_id=? ORDER BY id DESC LIMIT 1
    """, (student_id,)).fetchone()
    conn.close()
    return row


def update_subscription_paid(subscription_id, new_paid_amount):
    conn = get_connection()
    conn.execute("UPDATE subscriptions SET paid_amount=? WHERE id=?",
                 (new_paid_amount, subscription_id))
    conn.commit()
    conn.close()


# ======================== FINANCE ========================

def add_finance(tx_type, category, amount, notes, student_id=None):
    conn = get_connection()
    conn.execute(
        "INSERT INTO finance (type, category, amount, notes, student_id) VALUES (?, ?, ?, ?, ?)",
        (tx_type, category, amount, notes, student_id))
    conn.commit()
    conn.close()


def get_all_finance():
    conn = get_connection()
    rows = conn.execute("""
        SELECT f.*, s.name as student_name
        FROM finance f
        LEFT JOIN students s ON f.student_id = s.id
        ORDER BY f.id DESC
    """).fetchall()
    conn.close()
    return rows


def get_finance_summary():
    conn = get_connection()
    income = conn.execute("SELECT COALESCE(SUM(amount),0) FROM finance WHERE type='income'").fetchone()[0]
    expense = conn.execute("SELECT COALESCE(SUM(amount),0) FROM finance WHERE type='expense'").fetchone()[0]
    conn.close()
    return {"income": income, "expense": expense, "net": income - expense}


def get_total_center_debts():
    conn = get_connection()
    row = conn.execute("""
        SELECT COALESCE(SUM(total_required - paid_amount), 0) as total_debts
        FROM subscriptions
        WHERE total_required > paid_amount
    """).fetchone()
    conn.close()
    return row[0] if row else 0


def delete_finance(finance_id):
    conn = get_connection()
    conn.execute("DELETE FROM finance WHERE id=?", (finance_id,))
    conn.commit()
    conn.close()


# ======================== STUDENT LEDGER ========================

def add_ledger_entry(student_id, description, debit=0, credit=0):
    conn = get_connection()
    last = conn.execute(
        "SELECT balance FROM student_ledger WHERE student_id=? ORDER BY id DESC LIMIT 1",
        (student_id,)).fetchone()
    prev_balance = last['balance'] if last else 0
    new_balance = prev_balance + debit - credit
    conn.execute(
        "INSERT INTO student_ledger (student_id, description, debit, credit, balance) VALUES (?, ?, ?, ?, ?)",
        (student_id, description, debit, credit, new_balance))
    conn.commit()
    conn.close()


def get_student_ledger(student_id):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM student_ledger WHERE student_id=? ORDER BY id",
        (student_id,)).fetchall()
    conn.close()
    return rows


# ======================== ATTENDANCE ========================

def mark_attendance(student_id, group_id, status, att_date=None):
    conn = get_connection()
    if att_date is None:
        att_date = date.today().isoformat()
    existing = conn.execute(
        "SELECT id FROM attendance WHERE student_id=? AND date=?",
        (student_id, att_date)).fetchone()
    if existing:
        conn.execute("UPDATE attendance SET status=? WHERE id=?", (status, existing['id']))
    else:
        conn.execute(
            "INSERT INTO attendance (student_id, group_id, date, status) VALUES (?, ?, ?, ?)",
            (student_id, group_id, att_date, status))
    conn.commit()
    conn.close()


def get_attendance_for_date(group_id, att_date):
    conn = get_connection()
    rows = conn.execute("""
        SELECT a.*, s.name as student_name
        FROM attendance a
        JOIN students s ON a.student_id = s.id
        WHERE a.group_id=? AND a.date=?
    """, (group_id, att_date)).fetchall()
    conn.close()
    return rows


def get_student_attendance(student_id):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM attendance WHERE student_id=? ORDER BY date",
        (student_id,)).fetchall()
    conn.close()
    return rows


def get_student_attendance_for_month(student_id, year, month):
    conn = get_connection()
    month_str = f"{year}-{month:02d}"
    rows = conn.execute(
        "SELECT * FROM attendance WHERE student_id=? AND date LIKE ?",
        (student_id, f"{month_str}%")).fetchall()
    conn.close()
    return rows


# ======================== INVENTORY ========================

def add_inventory_item(item_name, stock, price):
    conn = get_connection()
    conn.execute("INSERT INTO inventory (item_name, stock, price) VALUES (?, ?, ?)",
                 (item_name, stock, price))
    conn.commit()
    conn.close()


def get_all_inventory():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM inventory ORDER BY id").fetchall()
    conn.close()
    return rows


def update_inventory_item(item_id, item_name, stock, price):
    conn = get_connection()
    conn.execute("UPDATE inventory SET item_name=?, stock=?, price=? WHERE id=?",
                 (item_name, stock, price, item_id))
    conn.commit()
    conn.close()


def delete_inventory_item(item_id):
    conn = get_connection()
    conn.execute("DELETE FROM inventory WHERE id=?", (item_id,))
    conn.commit()
    conn.close()


def sell_inventory_item(item_id, quantity, student_id=None):
    """Sell an item: deduct stock, add finance income, record in student ledger if applicable."""
    conn = get_connection()
    item = conn.execute("SELECT * FROM inventory WHERE id=?", (item_id,)).fetchone()
    if not item:
        conn.close()
        return False, "العنصر غير موجود"
    if item['stock'] < quantity:
        conn.close()
        return False, "الكمية غير كافية في المخزون"

    total_price = item['price'] * quantity
    new_stock = item['stock'] - quantity
    conn.execute("UPDATE inventory SET stock=? WHERE id=?", (new_stock, item_id))
    conn.execute(
        "INSERT INTO finance (type, category, amount, notes, student_id) VALUES (?, ?, ?, ?, ?)",
        ('income', 'مبيعات مخزون', total_price,
         f"بيع {quantity} x {item['item_name']}", student_id))

    if student_id:
        last = conn.execute(
            "SELECT balance FROM student_ledger WHERE student_id=? ORDER BY id DESC LIMIT 1",
            (student_id,)).fetchone()
        prev_balance = last['balance'] if last else 0
        new_balance = prev_balance + total_price
        conn.execute(
            "INSERT INTO student_ledger (student_id, description, debit, credit, balance) VALUES (?, ?, ?, ?, ?)",
            (student_id, f"شراء {quantity} x {item['item_name']}", total_price, 0, new_balance))

    conn.commit()
    conn.close()
    return True, f"تم البيع بنجاح - المبلغ: {total_price}"
