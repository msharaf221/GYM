import sys
import os
from PyQt6.QtWidgets import QApplication

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from main import StudentDashboard
from database import DatabaseManager

def test_retention():
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    db_name = 'test_retention.db'
    if os.path.exists(db_name): os.remove(db_name)
    db = DatabaseManager(db_name)

    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO students (name, status) VALUES ('Bad Student', 'Active')")
        student_id = cursor.lastrowid
        cursor.execute("INSERT INTO sessions (session_date, session_price) VALUES ('2023-10-01', 50), ('2023-10-02', 50)")
        s1, s2 = 1, 2
        cursor.execute("INSERT INTO attendance (student_id, session_id, status) VALUES (?, ?, 'Absent')", (student_id, s1))
        cursor.execute("INSERT INTO attendance (student_id, session_id, status) VALUES (?, ?, 'Absent')", (student_id, s2))

    app = QApplication(sys.argv)

    # Monkeypatch
    import database
    original_init = database.DatabaseManager.__init__
    database.DatabaseManager.__init__ = lambda self, db_path=db_name: original_init(self, db_name)

    window = StudentDashboard()
    window.load_retention_alarm()

    assert window.retention_table.rowCount() == 1
    assert window.retention_table.item(0, 2).text() == "2" # 2 consecutive absences

    print("Retention Alarm Test Passed!")
    os.remove(db_name)

if __name__ == "__main__":
    test_retention()
