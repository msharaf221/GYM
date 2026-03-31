import os
import sys
# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from database import DatabaseManager
from exports import ExcelExporter

def test_exports():
    db_name = 'test_exports.db'
    if os.path.exists(db_name): os.remove(db_name)
    db = DatabaseManager(db_name)

    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO students (name, phone) VALUES ('Alice', '123')")

    exporter = ExcelExporter(db)
    f1 = exporter.export_students("test_students.xlsx")
    assert os.path.exists(f1)

    print("Excel Export Test Passed!")
    os.remove(db_name)
    os.remove(f1)

if __name__ == "__main__":
    test_exports()
