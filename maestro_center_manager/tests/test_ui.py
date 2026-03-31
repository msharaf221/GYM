import sys
from PyQt6.QtWidgets import QApplication
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from main import StudentDashboard

def test_ui():
    app = QApplication(sys.argv)
    window = StudentDashboard()
    if window.windowTitle() == "Maestro Center Manager - Dashboard":
        print("Window title matches.")
    if window.student_table.columnCount() == 6:
        print("Table column count matches.")
    print("UI Test Passed!")

if __name__ == "__main__":
    test_ui()
