import sys
import os
from PyQt6.QtWidgets import QApplication

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from main import StudentDashboard
from database import DatabaseManager

def test_expenses():
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    db_name = 'test_expenses.db'
    if os.path.exists(db_name): os.remove(db_name)
    db = DatabaseManager(db_name)

    app = QApplication(sys.argv)

    # Monkeypatch
    import database
    original_init = database.DatabaseManager.__init__
    database.DatabaseManager.__init__ = lambda self, db_path=db_name: original_init(self, db_name)

    window = StudentDashboard()

    # Add an expense
    window.expense_desc.setText("Electricity Bill")
    window.expense_amount.setText("200")
    window.expense_category.setCurrentText("Electricity")
    window.expense_date.setText("2023-10-27")
    window.add_expense()

    assert window.expenses_table.rowCount() == 1
    assert window.expenses_table.item(0, 3).text() == "Electricity Bill"
    assert "200.00" in window.total_expense_label.text()

    print("Expenses Tracking Test Passed!")
    os.remove(db_name)

if __name__ == "__main__":
    test_expenses()
