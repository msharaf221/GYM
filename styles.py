"""
styles.py - Black & Gold Stylesheet for Mobile Shop Management System
"""

DARK_STYLE = """
/* ========== Global ========== */
QWidget {
    background-color: #0a0a0a;
    color: #e0e0e0;
    font-family: "Segoe UI", "Cairo", "Noto Sans Arabic", sans-serif;
    font-size: 14px;
}

/* ========== Main Window ========== */
QMainWindow {
    background-color: #0a0a0a;
}

/* ========== Sidebar ========== */
#sidebar {
    background-color: #111111;
    border-left: 2px solid #1a1a1a;
    min-width: 220px;
    max-width: 220px;
}

#sidebar QPushButton {
    background-color: transparent;
    color: #999999;
    border: none;
    border-radius: 8px;
    padding: 12px 16px;
    text-align: right;
    font-size: 14px;
    font-weight: 500;
    margin: 2px 8px;
}

#sidebar QPushButton:hover {
    background-color: #1a1a1a;
    color: #d4a017;
}

#sidebar QPushButton:checked,
#sidebar QPushButton[active="true"] {
    background-color: #1a1a1a;
    color: #d4a017;
    font-weight: 700;
    border-right: 3px solid #d4a017;
}

#sidebar_header {
    color: #d4a017;
    font-size: 18px;
    font-weight: bold;
    padding: 20px 12px;
}

#sidebar_user_label {
    color: #777777;
    font-size: 12px;
    padding: 4px 16px;
}

/* ========== Cards / Containers ========== */
QFrame#card {
    background-color: #111111;
    border-radius: 12px;
    border: 1px solid #222222;
    padding: 16px;
}

QFrame#stat_card {
    background-color: #111111;
    border-radius: 12px;
    border: 1px solid #2a2a2a;
    padding: 20px;
    min-width: 180px;
}

QFrame#stat_card QLabel#stat_value {
    font-size: 28px;
    font-weight: bold;
    color: #d4a017;
}

QFrame#stat_card QLabel#stat_label {
    font-size: 12px;
    color: #888888;
}

/* ========== Tables ========== */
QTableWidget {
    background-color: #111111;
    alternate-background-color: #0d0d0d;
    border: 1px solid #222222;
    border-radius: 8px;
    gridline-color: #1a1a1a;
    selection-background-color: #d4a017;
    selection-color: #000000;
    font-size: 13px;
}

QTableWidget::item {
    padding: 8px 12px;
    border-bottom: 1px solid #1a1a1a;
}

QHeaderView::section {
    background-color: #1a1a1a;
    color: #d4a017;
    padding: 10px 12px;
    border: none;
    font-weight: bold;
    font-size: 13px;
}

QTableWidget QTableCornerButton::section {
    background-color: #1a1a1a;
    border: none;
}

/* ========== Buttons ========== */
QPushButton {
    background-color: #d4a017;
    color: #000000;
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
    font-weight: 600;
    font-size: 13px;
}

QPushButton:hover {
    background-color: #e6b422;
}

QPushButton:pressed {
    background-color: #b8860b;
}

QPushButton:disabled {
    background-color: #333333;
    color: #666666;
}

QPushButton#btn_secondary {
    background-color: #1a1a1a;
    color: #d4a017;
    border: 1px solid #333333;
}

QPushButton#btn_secondary:hover {
    background-color: #252525;
    border-color: #d4a017;
}

QPushButton#btn_danger {
    background-color: #8b0000;
    color: #ffffff;
}

QPushButton#btn_danger:hover {
    background-color: #a00000;
}

QPushButton#btn_success {
    background-color: #1a7a1a;
    color: #ffffff;
}

QPushButton#btn_success:hover {
    background-color: #228b22;
}

/* ========== Input Fields ========== */
QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    background-color: #0d0d0d;
    border: 2px solid #222222;
    border-radius: 8px;
    padding: 8px 12px;
    color: #e0e0e0;
    font-size: 13px;
    selection-background-color: #d4a017;
    selection-color: #000000;
}

QLineEdit:focus, QTextEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
    border-color: #d4a017;
}

QComboBox::drop-down {
    border: none;
    padding-left: 8px;
}

QComboBox QAbstractItemView {
    background-color: #111111;
    border: 1px solid #333333;
    color: #e0e0e0;
    selection-background-color: #d4a017;
    selection-color: #000000;
}

/* ========== Labels ========== */
QLabel {
    color: #e0e0e0;
}

QLabel#section_title {
    font-size: 20px;
    font-weight: bold;
    color: #d4a017;
    padding-bottom: 8px;
}

QLabel#subtitle {
    font-size: 13px;
    color: #888888;
}

/* ========== ScrollBar ========== */
QScrollBar:vertical {
    border: none;
    background-color: #0a0a0a;
    width: 10px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background-color: #333333;
    border-radius: 5px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background-color: #d4a017;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

QScrollBar:horizontal {
    border: none;
    background-color: #0a0a0a;
    height: 10px;
}

QScrollBar::handle:horizontal {
    background-color: #333333;
    border-radius: 5px;
    min-width: 20px;
}

/* ========== Tab Widget ========== */
QTabWidget::pane {
    border: 1px solid #222222;
    border-radius: 8px;
    background-color: #111111;
}

QTabBar::tab {
    background-color: #0d0d0d;
    color: #888888;
    padding: 10px 20px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    margin-right: 2px;
}

QTabBar::tab:selected {
    background-color: #111111;
    color: #d4a017;
    font-weight: bold;
}

/* ========== Progress Bar ========== */
QProgressBar {
    border: 2px solid #222222;
    border-radius: 8px;
    text-align: center;
    color: #ffffff;
    font-weight: bold;
    background-color: #0d0d0d;
    min-height: 24px;
}

QProgressBar::chunk {
    background-color: #1a7a1a;
    border-radius: 6px;
}

QProgressBar[warning="true"]::chunk {
    background-color: #d4a017;
}

QProgressBar[danger="true"]::chunk {
    background-color: #8b0000;
}

/* ========== Dialog ========== */
QDialog {
    background-color: #0a0a0a;
}

QMessageBox {
    background-color: #0a0a0a;
}

QMessageBox QLabel {
    color: #e0e0e0;
}

/* ========== Group Box ========== */
QGroupBox {
    border: 1px solid #222222;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 16px;
    font-weight: bold;
    color: #d4a017;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top right;
    padding: 0 8px;
}

/* ========== Date Edit ========== */
QDateEdit {
    background-color: #0d0d0d;
    border: 2px solid #222222;
    border-radius: 8px;
    padding: 8px 12px;
    color: #e0e0e0;
}

QDateEdit:focus {
    border-color: #d4a017;
}

QCalendarWidget {
    background-color: #111111;
}

/* ========== ToolTip ========== */
QToolTip {
    background-color: #1a1a1a;
    color: #d4a017;
    border: 1px solid #d4a017;
    border-radius: 4px;
    padding: 4px 8px;
}
"""
