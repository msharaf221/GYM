import sqlite3
import os

class DatabaseManager:
    def __init__(self, db_path='maestro_center.db'):
        self.db_path = db_path
        self.init_db()

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Families table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS families (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    family_name TEXT NOT NULL,
                    discount_rate REAL DEFAULT 0.0
                )
            ''')

            # Grades table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS grades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE
                )
            ''')

            # Teachers table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS teachers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    phone TEXT,
                    commission_rate REAL DEFAULT 0.0
                )
            ''')

            # Students table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS students (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    phone TEXT,
                    barcode TEXT UNIQUE,
                    grade_id INTEGER,
                    family_id INTEGER,
                    status TEXT DEFAULT 'Active',
                    FOREIGN KEY (grade_id) REFERENCES grades (id),
                    FOREIGN KEY (family_id) REFERENCES families (id)
                )
            ''')

            # Books table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS books (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL UNIQUE,
                    price REAL NOT NULL,
                    stock_quantity INTEGER DEFAULT 0
                )
            ''')

            # Sessions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    teacher_id INTEGER,
                    grade_id INTEGER,
                    session_date TEXT NOT NULL,
                    session_price REAL NOT NULL,
                    FOREIGN KEY (teacher_id) REFERENCES teachers (id),
                    FOREIGN KEY (grade_id) REFERENCES grades (id)
                )
            ''')

            # Attendance table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS attendance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER,
                    session_id INTEGER,
                    status TEXT DEFAULT 'Present',
                    FOREIGN KEY (student_id) REFERENCES students (id),
                    FOREIGN KEY (session_id) REFERENCES sessions (id)
                )
            ''')

            # Invoices table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS invoices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER,
                    total_amount REAL NOT NULL,
                    paid_amount REAL NOT NULL,
                    previous_debt REAL DEFAULT 0.0,
                    date TEXT NOT NULL,
                    FOREIGN KEY (student_id) REFERENCES students (id)
                )
            ''')

            # Invoice Items table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS invoice_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    invoice_id INTEGER,
                    item_type TEXT NOT NULL, -- 'Fee', 'Book', 'Debt'
                    item_id INTEGER, -- Refers to Session ID or Book ID or None
                    amount REAL NOT NULL,
                    FOREIGN KEY (invoice_id) REFERENCES invoices (id)
                )
            ''')

            # Expenses table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    description TEXT NOT NULL,
                    amount REAL NOT NULL,
                    date TEXT NOT NULL,
                    category TEXT NOT NULL, -- 'Salary', 'Rent', 'Electricity', etc.
                    staff_id INTEGER, -- Optional link to a teacher/staff member
                    FOREIGN KEY (staff_id) REFERENCES teachers (id)
                )
            ''')

            conn.commit()

    def promote_student(self, student_id, new_grade_id):
        """
        Promotes a student to a new grade.
        All attendance and payment history is preserved by their references to the student_id.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE students SET grade_id = ? WHERE id = ?", (new_grade_id, student_id))
            conn.commit()

    def get_student_history(self, student_id):
        """
        Retrieves a student's full attendance and payment history.
        """
        history = {
            'attendance': [],
            'payments': []
        }
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Attendance
            cursor.execute("""
                SELECT s.session_date, g.name, a.status
                FROM attendance a
                JOIN sessions s ON a.session_id = s.id
                JOIN grades g ON s.grade_id = g.id
                WHERE a.student_id = ?
                ORDER BY s.session_date DESC
            """, (student_id,))
            history['attendance'] = cursor.fetchall()

            # Payments (Invoices)
            cursor.execute("""
                SELECT i.date, i.total_amount, i.paid_amount, i.previous_debt
                FROM invoices i
                WHERE i.student_id = ?
                ORDER BY i.date DESC
            """, (student_id,))
            history['payments'] = cursor.fetchall()

        return history

if __name__ == "__main__":
    db_manager = DatabaseManager()
    print("Database initialized successfully.")
