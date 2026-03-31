import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QColor

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from main import StudentDashboard
from database import DatabaseManager

def test_attendance_grid():
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    db_name = 'test_attn_grid.db'
    if os.path.exists(db_name): os.remove(db_name)
    db = DatabaseManager(db_name)

    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO grades (name) VALUES ('Grade A')")
        grade_id = cursor.lastrowid
        cursor.execute("INSERT INTO students (name, grade_id) VALUES ('Bob', ?)", (grade_id,))
        cursor.execute("INSERT INTO sessions (grade_id, session_date, session_price) VALUES (?, '2023-10-01', 50)", (grade_id,))
        session_id = cursor.lastrowid
        cursor.execute("INSERT INTO attendance (student_id, session_id, status) VALUES (1, ?, 'Present')", (session_id,))

    app = QApplication(sys.argv)
    # Monkeypatch DatabaseManager to use test_attn_grid.db
    import database
    original_init = database.DatabaseManager.__init__
    database.DatabaseManager.__init__ = lambda self, db_path=db_name: original_init(self, db_name)

    window = StudentDashboard()

    # Simulate selecting grade
    # find the index for 'Grade A'
    idx = window.grade_filter.findText('Grade A')
    window.grade_filter.setCurrentIndex(idx)
    window.load_attendance_grid()

    # Check grid
    print(f"Row count: {window.attendance_grid.rowCount()}")
    print(f"Col count: {window.attendance_grid.columnCount()}")

    assert window.attendance_grid.rowCount() == 1
    assert window.attendance_grid.columnCount() == 2 # Name + 1 session

    color = window.attendance_grid.item(0, 1).background().color()
    print(f"Color: {color.name()}")
    assert color.name() == QColor("green").name()

    print("Attendance Grid Logic Test Passed!")
    os.remove(db_name)

if __name__ == "__main__":
    test_attendance_grid()
