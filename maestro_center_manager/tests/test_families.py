import sys
import os
from PyQt6.QtWidgets import QApplication

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from main import StudentDashboard
from database import DatabaseManager

def test_families():
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    db_name = 'test_families.db'
    if os.path.exists(db_name): os.remove(db_name)
    db = DatabaseManager(db_name)

    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO families (family_name, discount_rate) VALUES ('Smith', 15)")
        fam_id = cursor.lastrowid
        cursor.execute("INSERT INTO students (name, family_id) VALUES ('Alice Smith', ?)", (fam_id,))
        student_id = cursor.lastrowid

    app = QApplication(sys.argv)

    # Monkeypatch
    import database
    original_init = database.DatabaseManager.__init__
    database.DatabaseManager.__init__ = lambda self, db_path=db_name: original_init(self, db_name)

    window = StudentDashboard()

    discount = window.get_sibling_discount(student_id)
    assert discount == 15.0

    print("Sibling Linker / Discount Test Passed!")
    os.remove(db_name)

if __name__ == "__main__":
    test_families()
