import sys
import os
from PyQt6.QtWidgets import QApplication

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from main import StudentDashboard
from database import DatabaseManager

def test_books():
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    db_name = 'test_books.db'
    if os.path.exists(db_name): os.remove(db_name)
    db = DatabaseManager(db_name)

    app = QApplication(sys.argv)

    # Monkeypatch
    import database
    original_init = database.DatabaseManager.__init__
    database.DatabaseManager.__init__ = lambda self, db_path=db_name: original_init(self, db_name)

    window = StudentDashboard()

    # Add a book via UI logic
    window.book_title.setText("Physics 101")
    window.book_price.setText("150")
    window.book_stock.setText("10")
    window.add_book()

    assert window.books_table.rowCount() == 1
    assert window.books_table.item(0, 1).text() == "Physics 101"

    # Check revenue calculation logic
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO invoices (student_id, total_amount, paid_amount, date) VALUES (1, 150, 150, '2023-10-01')")
        inv_id = cursor.lastrowid
        cursor.execute("INSERT INTO invoice_items (invoice_id, item_type, item_id, amount) VALUES (?, 'Book', 1, 150)", (inv_id,))

    window.update_book_revenue()
    assert "150.00" in window.revenue_label.text()

    print("Book Inventory Test Passed!")
    os.remove(db_name)

if __name__ == "__main__":
    test_books()
