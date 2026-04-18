"""
main.py - Entry point for Mobile Shop & Digital Wallet Management System
Handles: Login screen, main window with sidebar navigation, user management.
"""

import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QDialog, QFormLayout, QMessageBox,
    QStackedWidget, QFrame, QComboBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QSizePolicy,
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont

import database as db
from styles import DARK_STYLE
from ui_inventory import InventoryPage
from ui_maintenance import MaintenancePage
from ui_wallets import WalletsPage
from ui_accounting import AccountingPage


class LoginDialog(QDialog):
    """Login dialog with username/password authentication."""

    def __init__(self):
        super().__init__()
        self.user = None
        self.setWindowTitle("تسجيل الدخول - موبايل شوب")
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setFixedSize(400, 350)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(40, 40, 40, 40)

        # Logo / Title
        title = QLabel("موبايل شوب")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #e94560; margin-bottom: 8px;")
        layout.addWidget(title)

        subtitle = QLabel("نظام إدارة المحل والمحافظ الرقمية")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setObjectName("subtitle")
        layout.addWidget(subtitle)

        layout.addSpacing(20)

        # Username
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("اسم المستخدم")
        self.username_input.setMinimumHeight(40)
        layout.addWidget(self.username_input)

        # Password
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("كلمة المرور")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setMinimumHeight(40)
        self.password_input.returnPressed.connect(self._login)
        layout.addWidget(self.password_input)

        # Login button
        btn_login = QPushButton("دخول")
        btn_login.setMinimumHeight(42)
        btn_login.clicked.connect(self._login)
        layout.addWidget(btn_login)

        # Error label
        self.error_label = QLabel("")
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_label.setStyleSheet("color: #e94560;")
        layout.addWidget(self.error_label)

        layout.addStretch()

    def _login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()
        if not username or not password:
            self.error_label.setText("يرجى إدخال اسم المستخدم وكلمة المرور")
            return
        user = db.authenticate(username, password)
        if user:
            self.user = dict(user)
            self.accept()
        else:
            self.error_label.setText("اسم المستخدم أو كلمة المرور غير صحيحة")
            self.password_input.clear()
            self.password_input.setFocus()


class MainWindow(QMainWindow):
    """Main application window with sidebar navigation."""

    def __init__(self, user):
        super().__init__()
        self.user = user
        self.setWindowTitle("موبايل شوب - نظام الإدارة")
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setMinimumSize(1200, 750)
        self._setup_ui()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)

        # Sidebar header
        header = QLabel("موبايل شوب")
        header.setObjectName("sidebar_header")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sidebar_layout.addWidget(header)

        user_label = QLabel(f"مرحباً، {self.user['username']} ({self.user['role']})")
        user_label.setObjectName("sidebar_user_label")
        user_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sidebar_layout.addWidget(user_label)

        sidebar_layout.addSpacing(16)

        # Navigation buttons
        self.nav_buttons = []
        self.stack = QStackedWidget()

        nav_items = [
            ("لوحة المعلومات", "dashboard"),
            ("المخزون", "inventory"),
            ("الصيانة", "maintenance"),
            ("المحافظ الرقمية", "wallets"),
        ]

        # Only show accounting to admin
        if self.user["role"] == "admin":
            nav_items.append(("المحاسبة", "accounting"))
            nav_items.append(("المستخدمون", "users"))

        for idx, (label, page_id) in enumerate(nav_items):
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, i=idx: self._navigate(i))
            sidebar_layout.addWidget(btn)
            self.nav_buttons.append(btn)

        sidebar_layout.addStretch()

        # Logout button
        btn_logout = QPushButton("تسجيل الخروج")
        btn_logout.setObjectName("btn_danger")
        btn_logout.clicked.connect(self._logout)
        sidebar_layout.addWidget(btn_logout)
        sidebar_layout.addSpacing(12)

        main_layout.addWidget(sidebar)

        # Content pages
        role = self.user["role"]

        # Dashboard (accounting page with read-only for staff)
        self.accounting_page = AccountingPage(role)
        self.stack.addWidget(self.accounting_page)

        # Inventory
        self.inventory_page = InventoryPage(role)
        self.stack.addWidget(self.inventory_page)

        # Maintenance
        self.maintenance_page = MaintenancePage(role)
        self.stack.addWidget(self.maintenance_page)

        # Wallets
        self.wallets_page = WalletsPage(role)
        self.stack.addWidget(self.wallets_page)

        if role == "admin":
            # Full accounting (same page, already added as dashboard)
            accounting_full = AccountingPage(role)
            self.stack.addWidget(accounting_full)

            # User management
            users_page = UsersPage()
            self.stack.addWidget(users_page)

        main_layout.addWidget(self.stack)

        # Select first page
        self._navigate(0)

    def _navigate(self, index):
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)
            btn.setProperty("active", i == index)
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        self.stack.setCurrentIndex(index)

        # Refresh page data when navigating
        widget = self.stack.widget(index)
        if hasattr(widget, 'refresh_table'):
            widget.refresh_table()
        elif hasattr(widget, 'refresh_all'):
            widget.refresh_all()

    def _logout(self):
        reply = QMessageBox.question(
            self, "تسجيل الخروج",
            "هل أنت متأكد من تسجيل الخروج؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.close()
            run_app()


class UsersPage(QWidget):
    """User management page (Admin only)."""

    def __init__(self):
        super().__init__()
        self._setup_ui()
        self.refresh_table()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        header = QHBoxLayout()
        title = QLabel("إدارة المستخدمين")
        title.setObjectName("section_title")
        header.addWidget(title)
        header.addStretch()

        btn_add = QPushButton("+ إضافة مستخدم")
        btn_add.clicked.connect(self._add_user)
        header.addWidget(btn_add)
        layout.addLayout(header)

        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "اسم المستخدم", "الصلاحية", "تاريخ الإنشاء", "إجراءات"])
        self.table.setColumnHidden(0, True)
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

    def refresh_table(self):
        users = db.get_all_users()
        self.table.setRowCount(len(users))
        for row, user in enumerate(users):
            self.table.setItem(row, 0, QTableWidgetItem(user["id"]))
            self.table.setItem(row, 1, QTableWidgetItem(user["username"]))
            role_text = "مدير" if user["role"] == "admin" else "موظف"
            self.table.setItem(row, 2, QTableWidgetItem(role_text))
            self.table.setItem(row, 3, QTableWidgetItem(user["created_at"] or ""))

            actions = QWidget()
            actions_layout = QHBoxLayout(actions)
            actions_layout.setContentsMargins(4, 4, 4, 4)

            btn_del = QPushButton("حذف")
            btn_del.setObjectName("btn_danger")
            btn_del.setFixedWidth(60)
            btn_del.clicked.connect(lambda _, uid=user["id"], uname=user["username"]: self._delete_user(uid, uname))
            actions_layout.addWidget(btn_del)

            self.table.setCellWidget(row, 4, actions)

    def _add_user(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("إضافة مستخدم جديد")
        dlg.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        dlg.setMinimumWidth(350)
        form = QFormLayout(dlg)

        username_edit = QLineEdit()
        username_edit.setPlaceholderText("اسم المستخدم")
        form.addRow("المستخدم:", username_edit)

        password_edit = QLineEdit()
        password_edit.setPlaceholderText("كلمة المرور")
        password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("كلمة المرور:", password_edit)

        role_combo = QComboBox()
        role_combo.addItem("مدير", "admin")
        role_combo.addItem("موظف", "staff")
        form.addRow("الصلاحية:", role_combo)

        btns = QHBoxLayout()
        btn_ok = QPushButton("إضافة")
        btn_ok.clicked.connect(dlg.accept)
        btn_cancel = QPushButton("إلغاء")
        btn_cancel.setObjectName("btn_secondary")
        btn_cancel.clicked.connect(dlg.reject)
        btns.addWidget(btn_ok)
        btns.addWidget(btn_cancel)
        form.addRow(btns)

        if dlg.exec() == QDialog.DialogCode.Accepted:
            username = username_edit.text().strip()
            password = password_edit.text()
            role = role_combo.currentData()
            if not username or not password:
                QMessageBox.warning(self, "تنبيه", "جميع الحقول مطلوبة")
                return
            try:
                db.add_user(username, password, role)
                self.refresh_table()
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"فشل إضافة المستخدم: {e}")

    def _delete_user(self, user_id, username):
        if username == "admin":
            QMessageBox.warning(self, "تنبيه", "لا يمكن حذف المدير الرئيسي")
            return
        reply = QMessageBox.question(
            self, "تأكيد الحذف",
            f"هل أنت متأكد من حذف المستخدم '{username}'؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            db.delete_user(user_id)
            self.refresh_table()


def run_app():
    """Show login dialog and launch main window on success."""
    login = LoginDialog()
    if login.exec() == QDialog.DialogCode.Accepted and login.user:
        window = MainWindow(login.user)
        window.showMaximized()
        # Keep reference to prevent GC
        app = QApplication.instance()
        if app:
            app._main_window = window


def main():
    # Initialize database
    db.init_db()

    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_STYLE)
    app.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

    # Set default font with Arabic support
    font = QFont("Segoe UI", 12)
    app.setFont(font)

    run_app()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
