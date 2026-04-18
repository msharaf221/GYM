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


DARK_STYLESHEET = """
    * {
        font-family: 'Segoe UI', 'Cairo', 'Arial', sans-serif;
        font-size: 13px;
    }
    QMainWindow, QWidget {
        background-color: #1e1e2e;
        color: #cdd6f4;
    }
    QLabel {
        color: #cdd6f4;
    }
    QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QDateEdit, QTimeEdit {
        background-color: #313244;
        color: #cdd6f4;
        border: 1px solid #45475a;
        border-radius: 5px;
        padding: 6px 10px;
        min-height: 28px;
    }
    QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
        border: 1px solid #00bcd4;
    }
    QComboBox::drop-down {
        border: none;
        width: 25px;
    }
    QComboBox QAbstractItemView {
        background-color: #313244;
        color: #cdd6f4;
        selection-background-color: #00bcd4;
    }
    QPushButton {
        background-color: #45475a;
        color: #cdd6f4;
        border: none;
        border-radius: 5px;
        padding: 8px 16px;
        min-height: 28px;
    }
    QPushButton:hover {
        background-color: #585b70;
    }
    QPushButton:pressed {
        background-color: #00bcd4;
        color: #1e1e2e;
    }
    QTableWidget {
        background-color: #1e1e2e;
        color: #cdd6f4;
        gridline-color: #313244;
        border: 1px solid #313244;
        border-radius: 5px;
        selection-background-color: #45475a;
    }
    QTableWidget::item {
        padding: 5px;
    }
    QHeaderView::section {
        background-color: #313244;
        color: #00bcd4;
        padding: 8px;
        border: 1px solid #45475a;
        font-weight: bold;
    }
    QTabWidget::pane {
        border: 1px solid #313244;
        border-radius: 5px;
        background-color: #1e1e2e;
    }
    QTabBar::tab {
        background-color: #313244;
        color: #cdd6f4;
        padding: 8px 20px;
        border-top-left-radius: 5px;
        border-top-right-radius: 5px;
        margin-right: 2px;
    }
    QTabBar::tab:selected {
        background-color: #00bcd4;
        color: #1e1e2e;
    }
    QGroupBox {
        border: 1px solid #45475a;
        border-radius: 8px;
        margin-top: 10px;
        padding: 15px;
        padding-top: 25px;
        color: #cdd6f4;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        left: 15px;
        padding: 0 5px;
        color: #00bcd4;
    }
    QCheckBox {
        color: #cdd6f4;
        spacing: 8px;
    }
    QCheckBox::indicator {
        width: 18px;
        height: 18px;
        border-radius: 3px;
        border: 2px solid #45475a;
        background-color: #313244;
    }
    QCheckBox::indicator:checked {
        background-color: #00bcd4;
        border-color: #00bcd4;
    }
    QScrollBar:vertical {
        background: #1e1e2e;
        width: 10px;
        border-radius: 5px;
    }
    QScrollBar::handle:vertical {
        background: #45475a;
        border-radius: 5px;
        min-height: 20px;
    }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        height: 0;
    }
    QMessageBox {
        background-color: #1e1e2e;
    }
    QDialog {
        background-color: #1e1e2e;
        color: #cdd6f4;
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
        color: #a6adc8;
    }
    QPushButton:hover {
        background-color: #313244;
        color: #cdd6f4;
    }
"""

SIDEBAR_ACTIVE = """
    text-align: right;
    padding: 12px 20px;
    border-radius: 0;
    font-size: 15px;
    border: none;
    background-color: #00bcd4;
    color: #1e1e2e;
    font-weight: bold;
    border-right: 4px solid #0097a7;
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
                background-color: #181825;
                border-left: 1px solid #313244;
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
            color: #00bcd4;
            padding: 20px;
            background-color: #11111b;
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
        ver.setStyleSheet("color: #585b70; padding: 10px; font-size: 11px;")
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
    app.setStyleSheet(DARK_STYLESHEET)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
