"""
Maestro ERP - Main Application
Educational Center Management System
Dark Modern UI with Sidebar Navigation and Stacked Widgets.
"""

import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QStackedWidget, QLabel, QFrame
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QIcon

import database_manager as db
from ui_students import StudentsWidget
from ui_finances import FinancesWidget
from ui_inventory import InventoryWidget
from ui_settings import SettingsWidget


LIGHT_STYLESHEET = """
    * {
        font-family: 'Segoe UI', 'Cairo', 'Arial', sans-serif;
        font-size: 13px;
    }
    QMainWindow, QWidget {
        background-color: #f5f7fa;
        color: #2c3e50;
    }
    QLabel {
        color: #2c3e50;
    }
    QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QDateEdit, QTimeEdit {
        background-color: #ffffff;
        color: #2c3e50;
        border: 1px solid #d0d7e2;
        border-radius: 5px;
        padding: 6px 10px;
        min-height: 28px;
    }
    QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
        border: 1px solid #3498db;
    }
    QComboBox::drop-down {
        border: none;
        width: 25px;
    }
    QComboBox QAbstractItemView {
        background-color: #ffffff;
        color: #2c3e50;
        selection-background-color: #3498db;
        selection-color: #ffffff;
    }
    QPushButton {
        background-color: #e8ecf1;
        color: #2c3e50;
        border: none;
        border-radius: 5px;
        padding: 8px 16px;
        min-height: 28px;
    }
    QPushButton:hover {
        background-color: #d0d7e2;
    }
    QPushButton:pressed {
        background-color: #3498db;
        color: #ffffff;
    }
    QTableWidget {
        background-color: #ffffff;
        color: #2c3e50;
        gridline-color: #e8ecf1;
        border: 1px solid #d0d7e2;
        border-radius: 5px;
        selection-background-color: #d6eaf8;
    }
    QTableWidget::item {
        padding: 5px;
    }
    QHeaderView::section {
        background-color: #e8ecf1;
        color: #2980b9;
        padding: 8px;
        border: 1px solid #d0d7e2;
        font-weight: bold;
    }
    QTabWidget::pane {
        border: 1px solid #d0d7e2;
        border-radius: 5px;
        background-color: #f5f7fa;
    }
    QTabBar::tab {
        background-color: #e8ecf1;
        color: #2c3e50;
        padding: 8px 20px;
        border-top-left-radius: 5px;
        border-top-right-radius: 5px;
        margin-right: 2px;
    }
    QTabBar::tab:selected {
        background-color: #3498db;
        color: #ffffff;
    }
    QGroupBox {
        border: 1px solid #d0d7e2;
        border-radius: 8px;
        margin-top: 10px;
        padding: 15px;
        padding-top: 25px;
        color: #2c3e50;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        left: 15px;
        padding: 0 5px;
        color: #2980b9;
    }
    QCheckBox {
        color: #2c3e50;
        spacing: 8px;
    }
    QCheckBox::indicator {
        width: 18px;
        height: 18px;
        border-radius: 3px;
        border: 2px solid #d0d7e2;
        background-color: #ffffff;
    }
    QCheckBox::indicator:checked {
        background-color: #3498db;
        border-color: #3498db;
    }
    QScrollBar:vertical {
        background: #f5f7fa;
        width: 10px;
        border-radius: 5px;
    }
    QScrollBar::handle:vertical {
        background: #c0c8d4;
        border-radius: 5px;
        min-height: 20px;
    }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        height: 0;
    }
    QMessageBox {
        background-color: #f5f7fa;
    }
    QDialog {
        background-color: #f5f7fa;
        color: #2c3e50;
    }
"""

SIDEBAR_STYLE = """
    QPushButton {
        text-align: right;
        padding: 12px 20px;
        border-radius: 0;
        font-size: 15px;
        border: none;
        background-color: transparent;
        color: #5d6d7e;
    }
    QPushButton:hover {
        background-color: #e8ecf1;
        color: #2c3e50;
    }
"""

SIDEBAR_ACTIVE = """
    text-align: right;
    padding: 12px 20px;
    border-radius: 0;
    font-size: 15px;
    border: none;
    background-color: #3498db;
    color: #ffffff;
    font-weight: bold;
    border-right: 4px solid #2176ad;
"""


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Maestro ERP - نظام ادارة المراكز التعليمية")
        self.setMinimumSize(1200, 700)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar
        sidebar = QFrame()
        sidebar.setFixedWidth(220)
        sidebar.setStyleSheet("""
            QFrame {
                background-color: #eaeff5;
                border-left: 1px solid #d0d7e2;
            }
        """ + SIDEBAR_STYLE)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)

        # Logo
        logo = QLabel("Maestro ERP")
        logo.setStyleSheet("""
            font-size: 20px;
            font-weight: bold;
            color: #2980b9;
            padding: 20px;
            background-color: #dce4ed;
        """)
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sidebar_layout.addWidget(logo)

        # Navigation buttons
        self.nav_buttons = []
        nav_items = [
            ("الطلاب", 0),
            ("الخزينة المالية", 1),
            ("المخزون", 2),
            ("الاعدادات", 3),
        ]

        for text, index in nav_items:
            btn = QPushButton(text)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _, idx=index: self.switch_page(idx))
            sidebar_layout.addWidget(btn)
            self.nav_buttons.append(btn)

        sidebar_layout.addStretch()

        # Version label
        ver = QLabel("v1.0.0")
        ver.setStyleSheet("color: #95a5b6; padding: 10px; font-size: 11px;")
        ver.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sidebar_layout.addWidget(ver)

        main_layout.addWidget(sidebar)

        # Stacked pages
        self.stack = QStackedWidget()
        self.students_page = StudentsWidget()
        self.finances_page = FinancesWidget()
        self.inventory_page = InventoryWidget()
        self.settings_page = SettingsWidget()

        self.stack.addWidget(self.students_page)
        self.stack.addWidget(self.finances_page)
        self.stack.addWidget(self.inventory_page)
        self.stack.addWidget(self.settings_page)

        main_layout.addWidget(self.stack)

        # Default page
        self.switch_page(0)

    def switch_page(self, index):
        self.stack.setCurrentIndex(index)
        for i, btn in enumerate(self.nav_buttons):
            if i == index:
                btn.setStyleSheet(SIDEBAR_ACTIVE)
            else:
                btn.setStyleSheet("")

        # Refresh page data
        widget = self.stack.widget(index)
        if hasattr(widget, 'refresh'):
            widget.refresh()
        if hasattr(widget, 'refresh_all'):
            widget.refresh_all()


def main():
    # Initialize database
    db.initialize_database()

    app = QApplication(sys.argv)
    app.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    app.setStyleSheet(LIGHT_STYLESHEET)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
