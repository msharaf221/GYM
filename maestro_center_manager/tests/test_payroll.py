import sys
import os
from PyQt6.QtWidgets import QApplication

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from main import StudentDashboard
from database import DatabaseManager

def test_payroll():
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    db_name = 'test_payroll.db'
    if os.path.exists(db_name): os.remove(db_name)
    db = DatabaseManager(db_name)

    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO teachers (name, commission_rate) VALUES ('Prof. X', 10)") # 10% commission
        teacher_id = cursor.lastrowid
        cursor.execute("INSERT INTO sessions (teacher_id, session_date, session_price) VALUES (?, '2023-10-01', 100)", (teacher_id,))
        session_id = cursor.lastrowid
        # Add 2 students
        cursor.execute("INSERT INTO attendance (student_id, session_id, status) VALUES (1, ?, 'Present')", (session_id,))
        cursor.execute("INSERT INTO attendance (student_id, session_id, status) VALUES (2, ?, 'Present')", (session_id,))

    app = QApplication(sys.argv)

    # Monkeypatch
    import database
    original_init = database.DatabaseManager.__init__
    database.DatabaseManager.__init__ = lambda self, db_path=db_name: original_init(self, db_name)

    window = StudentDashboard()

    # Select teacher
    idx = window.teacher_select.findText('Prof. X')
    window.teacher_select.setCurrentIndex(idx)
    window.calculate_payroll()

    # 2 students * 100 price = 200 total
    # 200 - 10% = 180 teacher pay
    pay_text = window.payroll_table.item(0, 3).text()
    assert pay_text == "180.00"
    assert "180.00" in window.total_pay_label.text()

    print("Teacher Payroll Test Passed!")
    os.remove(db_name)

if __name__ == "__main__":
    test_payroll()
