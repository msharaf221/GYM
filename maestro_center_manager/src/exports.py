import pandas as pd
from database import DatabaseManager

class ExcelExporter:
    def __init__(self, db_manager):
        self.db = db_manager

    def export_students(self, filename="students_report.xlsx"):
        with self.db.get_connection() as conn:
            df = pd.read_sql_query("""
                SELECT s.id, s.name, s.phone, s.barcode, g.name as grade, f.family_name, s.status
                FROM students s
                LEFT JOIN grades g ON s.grade_id = g.id
                LEFT JOIN families f ON s.family_id = f.id
            """, conn)
            df.to_excel(filename, index=False)
        return filename

    def export_payments(self, filename="payments_report.xlsx"):
        with self.db.get_connection() as conn:
            df = pd.read_sql_query("""
                SELECT i.id, s.name as student, i.total_amount, i.paid_amount, i.previous_debt, i.date
                FROM invoices i
                JOIN students s ON i.student_id = s.id
            """, conn)
            df.to_excel(filename, index=False)
        return filename

    def export_attendance(self, filename="attendance_report.xlsx"):
        with self.db.get_connection() as conn:
            df = pd.read_sql_query("""
                SELECT s.name as student, sess.session_date, g.name as grade, a.status
                FROM attendance a
                JOIN students s ON a.student_id = s.id
                JOIN sessions sess ON a.session_id = sess.id
                JOIN grades g ON sess.grade_id = g.id
            """, conn)
            df.to_excel(filename, index=False)
        return filename
