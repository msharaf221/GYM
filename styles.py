"""
styles.py - Modern Dark Mode Stylesheet for Mobile Shop Management System
"""

DARK_STYLE = """
/* ========== Global ========== */
QWidget {
    background-color: #1a1a2e;
    color: #e0e0e0;
    font-family: "Segoe UI", "Cairo", "Noto Sans Arabic", sans-serif;
    font-size: 14px;
}

/* ========== Main Window ========== */
QMainWindow {
    background-color: #1a1a2e;
}

/* ========== Sidebar ========== */
#sidebar {
    background-color: #16213e;
    border-left: 2px solid #0f3460;
    min-width: 220px;
    max-width: 220px;
}

#sidebar QPushButton {
    background-color: transparent;
    color: #a0a0c0;
    border: none;
    border-radius: 8px;
    padding: 12px 16px;
    text-align: right;
    font-size: 14px;
    font-weight: 500;
    margin: 2px 8px;
}

#sidebar QPushButton:hover {
    background-color: #0f3460;
    color: #e94560;
}

#sidebar QPushButton:checked,
#sidebar QPushButton[active="true"] {
    background-color: #0f3460;
    color: #e94560;
    font-weight: 700;
    border-right: 3px solid #e94560;
}

#sidebar_header {
    color: #e94560;
    font-size: 18px;
    font-weight: bold;
    padding: 20px 12px;
}

#sidebar_user_label {
    color: #8888aa;
    font-size: 12px;
    padding: 4px 16px;
}

/* ========== Cards / Containers ========== */
QFrame#card {
    background-color: #16213e;
    border-radius: 12px;
    border: 1px solid #0f3460;
    padding: 16px;
}

QFrame#stat_card {
    background-color: #16213e;
    border-radius: 12px;
    border: 1px solid #0f3460;
    padding: 20px;
    min-width: 180px;
}

QFrame#stat_card QLabel#stat_value {
    font-size: 28px;
    font-weight: bold;
    color: #e94560;
}

QFrame#stat_card QLabel#stat_label {
    font-size: 12px;
    color: #8888aa;
}

/* ========== Tables ========== */
QTableWidget {
    background-color: #16213e;
    alternate-background-color: #1a1a36;
    border: 1px solid #0f3460;
    border-radius: 8px;
    gridline-color: #0f3460;
    selection-background-color: #e94560;
    selection-color: #ffffff;
    font-size: 13px;
}

QTableWidget::item {
    padding: 8px 12px;
    border-bottom: 1px solid #0f3460;
}

QHeaderView::section {
    background-color: #0f3460;
    color: #e0e0e0;
    padding: 10px 12px;
    border: none;
    font-weight: bold;
    font-size: 13px;
}

QTableWidget QTableCornerButton::section {
    background-color: #0f3460;
    border: none;
}

/* ========== Buttons ========== */
QPushButton {
    background-color: #e94560;
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
    font-weight: 600;
    font-size: 13px;
}

QPushButton:hover {
    background-color: #c73e54;
}

QPushButton:pressed {
    background-color: #a83347;
}

QPushButton:disabled {
    background-color: #444466;
    color: #777799;
}

QPushButton#btn_secondary {
    background-color: #0f3460;
    color: #e0e0e0;
}

QPushButton#btn_secondary:hover {
    background-color: #1a4a7a;
}

QPushButton#btn_danger {
    background-color: #c0392b;
}

QPushButton#btn_danger:hover {
    background-color: #a93226;
}

QPushButton#btn_success {
    background-color: #27ae60;
}

QPushButton#btn_success:hover {
    background-color: #219a52;
}

/* ========== Input Fields ========== */
QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    background-color: #1a1a36;
    border: 2px solid #0f3460;
    border-radius: 8px;
    padding: 8px 12px;
    color: #e0e0e0;
    font-size: 13px;
    selection-background-color: #e94560;
}

QLineEdit:focus, QTextEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
    border-color: #e94560;
}

QComboBox::drop-down {
    border: none;
    padding-left: 8px;
}

QComboBox QAbstractItemView {
    background-color: #16213e;
    border: 1px solid #0f3460;
    color: #e0e0e0;
    selection-background-color: #e94560;
}

/* ========== Labels ========== */
QLabel {
    color: #e0e0e0;
}

QLabel#section_title {
    font-size: 20px;
    font-weight: bold;
    color: #e94560;
    padding-bottom: 8px;
}

QLabel#subtitle {
    font-size: 13px;
    color: #8888aa;
}

/* ========== ScrollBar ========== */
QScrollBar:vertical {
    border: none;
    background-color: #1a1a2e;
    width: 10px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background-color: #0f3460;
    border-radius: 5px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background-color: #e94560;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

QScrollBar:horizontal {
    border: none;
    background-color: #1a1a2e;
    height: 10px;
}

QScrollBar::handle:horizontal {
    background-color: #0f3460;
    border-radius: 5px;
    min-width: 20px;
}

/* ========== Tab Widget ========== */
QTabWidget::pane {
    border: 1px solid #0f3460;
    border-radius: 8px;
    background-color: #16213e;
}

QTabBar::tab {
    background-color: #1a1a36;
    color: #8888aa;
    padding: 10px 20px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    margin-right: 2px;
}

QTabBar::tab:selected {
    background-color: #16213e;
    color: #e94560;
    font-weight: bold;
}

/* ========== Progress Bar ========== */
QProgressBar {
    border: 2px solid #0f3460;
    border-radius: 8px;
    text-align: center;
    color: #ffffff;
    font-weight: bold;
    background-color: #1a1a36;
    min-height: 24px;
}

QProgressBar::chunk {
    background-color: #27ae60;
    border-radius: 6px;
}

QProgressBar[warning="true"]::chunk {
    background-color: #f39c12;
}

QProgressBar[danger="true"]::chunk {
    background-color: #e94560;
}

/* ========== Dialog ========== */
QDialog {
    background-color: #1a1a2e;
}

QMessageBox {
    background-color: #1a1a2e;
}

QMessageBox QLabel {
    color: #e0e0e0;
}

/* ========== Group Box ========== */
QGroupBox {
    border: 1px solid #0f3460;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 16px;
    font-weight: bold;
    color: #e94560;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top right;
    padding: 0 8px;
}

/* ========== Date Edit ========== */
QDateEdit {
    background-color: #1a1a36;
    border: 2px solid #0f3460;
    border-radius: 8px;
    padding: 8px 12px;
    color: #e0e0e0;
}

QDateEdit:focus {
    border-color: #e94560;
}

QCalendarWidget {
    background-color: #16213e;
}

/* ========== ToolTip ========== */
QToolTip {
    background-color: #0f3460;
    color: #e0e0e0;
    border: 1px solid #e94560;
    border-radius: 4px;
    padding: 4px 8px;
}
"""
