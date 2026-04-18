"""
ui_accounting.py - Multi-Vault Accounting System & Dashboard UI
Handles: vault management, transaction log, profit dashboard, transfers, daily reports.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QTableWidget, QTableWidgetItem, QDialog, QFormLayout, QDoubleSpinBox,
    QComboBox, QMessageBox, QHeaderView, QFrame, QGridLayout, QDateEdit,
    QTabWidget,
)
from PyQt6.QtCore import Qt, QDate

import database as db
from utils import format_currency


class AccountingPage(QWidget):
    """Main accounting and dashboard page."""

    def __init__(self, user_role="admin"):
        super().__init__()
        self.user_role = user_role
        self._setup_ui()
        self.refresh_all()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Tab widget
        tabs = QTabWidget()
        tabs.addTab(self._create_dashboard_tab(), "لوحة المعلومات")
        tabs.addTab(self._create_vaults_tab(), "الخزائن")
        tabs.addTab(self._create_transactions_tab(), "سجل المعاملات")
        layout.addWidget(tabs)

    def _create_dashboard_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(16)

        # Date filter
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("من:"))
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate.currentDate().addMonths(-1))
        filter_layout.addWidget(self.date_from)

        filter_layout.addWidget(QLabel("إلى:"))
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate())
        filter_layout.addWidget(self.date_to)

        btn_filter = QPushButton("تحديث")
        btn_filter.setObjectName("btn_secondary")
        btn_filter.clicked.connect(self.refresh_all)
        filter_layout.addWidget(btn_filter)
        filter_layout.addStretch()

        layout.addLayout(filter_layout)

        # Profit cards
        self.cards_frame = QFrame()
        self.cards_grid = QGridLayout(self.cards_frame)
        self.cards_grid.setSpacing(16)
        layout.addWidget(self.cards_frame)

        # Vault balances
        self.vaults_frame = QFrame()
        self.vaults_grid = QGridLayout(self.vaults_frame)
        self.vaults_grid.setSpacing(16)
        layout.addWidget(self.vaults_frame)

        layout.addStretch()
        return widget

    def _create_vaults_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(16)

        header = QHBoxLayout()
        title = QLabel("إدارة الخزائن")
        title.setObjectName("section_title")
        header.addWidget(title)
        header.addStretch()

        btn_transfer = QPushButton("تحويل بين الخزائن")
        btn_transfer.setObjectName("btn_secondary")
        btn_transfer.clicked.connect(self._transfer_dialog)
        header.addWidget(btn_transfer)

        if self.user_role == "admin":
            btn_adjust = QPushButton("تعديل رصيد")
            btn_adjust.clicked.connect(self._adjust_dialog)
            header.addWidget(btn_adjust)

        layout.addLayout(header)

        self.vaults_table = QTableWidget()
        self.vaults_table.setAlternatingRowColors(True)
        self.vaults_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.vaults_table.setColumnCount(4)
        self.vaults_table.setHorizontalHeaderLabels(["ID", "الخزنة", "النوع", "الرصيد"])
        self.vaults_table.setColumnHidden(0, True)
        self.vaults_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.vaults_table)

        return widget

    def _create_transactions_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(16)

        # Filters
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("الخزنة:"))
        self.txn_vault_filter = QComboBox()
        self.txn_vault_filter.addItem("الكل", None)
        filter_layout.addWidget(self.txn_vault_filter)

        filter_layout.addWidget(QLabel("النوع:"))
        self.txn_type_filter = QComboBox()
        self.txn_type_filter.addItem("الكل", None)
        for key, val in [
            ("sale", "بيع"), ("repair", "صيانة"), ("wallet_commission", "عمولة محفظة"),
            ("transfer_in", "تحويل وارد"), ("transfer_out", "تحويل صادر"), ("adjustment", "تعديل"),
        ]:
            self.txn_type_filter.addItem(val, key)
        filter_layout.addWidget(self.txn_type_filter)

        filter_layout.addWidget(QLabel("من:"))
        self.txn_date_from = QDateEdit()
        self.txn_date_from.setCalendarPopup(True)
        self.txn_date_from.setDate(QDate.currentDate().addMonths(-1))
        filter_layout.addWidget(self.txn_date_from)

        filter_layout.addWidget(QLabel("إلى:"))
        self.txn_date_to = QDateEdit()
        self.txn_date_to.setCalendarPopup(True)
        self.txn_date_to.setDate(QDate.currentDate())
        filter_layout.addWidget(self.txn_date_to)

        btn_filter = QPushButton("بحث")
        btn_filter.setObjectName("btn_secondary")
        btn_filter.clicked.connect(self._refresh_transactions)
        filter_layout.addWidget(btn_filter)

        layout.addLayout(filter_layout)

        self.txn_table = QTableWidget()
        self.txn_table.setAlternatingRowColors(True)
        self.txn_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.txn_table.horizontalHeader().setStretchLastSection(True)

        columns = ["ID", "الخزنة", "النوع", "المبلغ", "الوصف", "تاريخ الوردية", "وقت الإنشاء"]
        self.txn_table.setColumnCount(len(columns))
        self.txn_table.setHorizontalHeaderLabels(columns)
        self.txn_table.setColumnHidden(0, True)

        hdr = self.txn_table.horizontalHeader()
        for i in range(1, len(columns)):
            hdr.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)

        layout.addWidget(self.txn_table)

        return widget

    def refresh_all(self):
        self._refresh_dashboard()
        self._refresh_vaults()
        self._refresh_transactions()
        self._refresh_vault_filters()

    def _refresh_dashboard(self):
        from_date = self.date_from.date().toString("yyyy-MM-dd")
        to_date = self.date_to.date().toString("yyyy-MM-dd")
        summary = db.get_profit_summary(from_date, to_date)

        # Clear profit cards
        while self.cards_grid.count():
            child = self.cards_grid.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        cards_data = [
            ("أرباح الإكسسوارات", summary["accessory_profit"], "#27ae60"),
            ("أرباح الصيانة", summary["maintenance_profit"], "#3498db"),
            ("عمولات المحافظ", summary["wallet_commissions"], "#f39c12"),
            ("إجمالي الأرباح", summary["total"], "#e94560"),
        ]

        for idx, (label, value, color) in enumerate(cards_data):
            card = self._make_stat_card(label, value, color)
            self.cards_grid.addWidget(card, 0, idx)

        # Vault balances
        while self.vaults_grid.count():
            child = self.vaults_grid.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        vaults = db.get_all_vaults()
        vault_type_map = {"cash": "نقدي", "bank": "بنك", "digital": "رقمي"}
        for idx, v in enumerate(vaults):
            vtype = vault_type_map.get(v["vault_type"], v["vault_type"])
            card = self._make_stat_card(f"{v['name']} ({vtype})", v["balance"], "#0f3460")
            self.vaults_grid.addWidget(card, 0, idx)

    def _make_stat_card(self, label, value, color):
        card = QFrame()
        card.setObjectName("stat_card")
        card_layout = QVBoxLayout(card)

        val_lbl = QLabel(format_currency(value))
        val_lbl.setObjectName("stat_value")
        val_lbl.setStyleSheet(f"color: {color};")
        val_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(val_lbl)

        name_lbl = QLabel(label)
        name_lbl.setObjectName("stat_label")
        name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(name_lbl)

        return card

    def _refresh_vaults(self):
        vaults = db.get_all_vaults()
        vault_type_map = {"cash": "نقدي", "bank": "بنك", "digital": "رقمي"}
        self.vaults_table.setRowCount(len(vaults))
        for row, v in enumerate(vaults):
            self.vaults_table.setItem(row, 0, QTableWidgetItem(v["id"]))
            self.vaults_table.setItem(row, 1, QTableWidgetItem(v["name"]))
            self.vaults_table.setItem(row, 2, QTableWidgetItem(vault_type_map.get(v["vault_type"], "")))
            self.vaults_table.setItem(row, 3, QTableWidgetItem(format_currency(v["balance"])))

    def _refresh_vault_filters(self):
        self.txn_vault_filter.clear()
        self.txn_vault_filter.addItem("الكل", None)
        vaults = db.get_all_vaults()
        for v in vaults:
            self.txn_vault_filter.addItem(v["name"], v["id"])

    def _refresh_transactions(self):
        vault_id = self.txn_vault_filter.currentData() if hasattr(self, 'txn_vault_filter') else None
        source_type = self.txn_type_filter.currentData() if hasattr(self, 'txn_type_filter') else None
        from_date = self.txn_date_from.date().toString("yyyy-MM-dd") if hasattr(self, 'txn_date_from') else None
        to_date = self.txn_date_to.date().toString("yyyy-MM-dd") if hasattr(self, 'txn_date_to') else None

        txns = db.get_transactions(vault_id, from_date, to_date, source_type)

        type_map = {
            "sale": "بيع", "repair": "صيانة", "wallet_commission": "عمولة محفظة",
            "transfer_in": "تحويل وارد", "transfer_out": "تحويل صادر", "adjustment": "تعديل",
        }

        self.txn_table.setRowCount(len(txns))
        for row, txn in enumerate(txns):
            self.txn_table.setItem(row, 0, QTableWidgetItem(txn["id"]))
            self.txn_table.setItem(row, 1, QTableWidgetItem(txn["vault_name"]))
            self.txn_table.setItem(row, 2, QTableWidgetItem(type_map.get(txn["source_type"], txn["source_type"])))
            self.txn_table.setItem(row, 3, QTableWidgetItem(format_currency(txn["amount"])))
            self.txn_table.setItem(row, 4, QTableWidgetItem(txn["description"] or ""))
            self.txn_table.setItem(row, 5, QTableWidgetItem(txn["shift_date"] or ""))
            self.txn_table.setItem(row, 6, QTableWidgetItem(txn["created_at"] or ""))

    def _transfer_dialog(self):
        vaults = db.get_all_vaults()
        if len(vaults) < 2:
            QMessageBox.warning(self, "تنبيه", "يجب وجود خزنتين على الأقل")
            return

        dlg = QDialog(self)
        dlg.setWindowTitle("تحويل بين الخزائن")
        dlg.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        dlg.setMinimumWidth(400)
        form = QFormLayout(dlg)

        from_combo = QComboBox()
        to_combo = QComboBox()
        for v in vaults:
            from_combo.addItem(f"{v['name']} ({format_currency(v['balance'])})", v["id"])
            to_combo.addItem(v["name"], v["id"])
        form.addRow("من خزنة:", from_combo)
        form.addRow("إلى خزنة:", to_combo)

        amount_spin = QDoubleSpinBox()
        amount_spin.setMaximum(99999999)
        amount_spin.setDecimals(2)
        form.addRow("المبلغ:", amount_spin)

        desc_edit = QLineEdit()
        desc_edit.setPlaceholderText("وصف (اختياري)")
        form.addRow("الوصف:", desc_edit)

        btns = QHBoxLayout()
        btn_ok = QPushButton("تحويل")
        btn_ok.clicked.connect(dlg.accept)
        btn_cancel = QPushButton("إلغاء")
        btn_cancel.setObjectName("btn_secondary")
        btn_cancel.clicked.connect(dlg.reject)
        btns.addWidget(btn_ok)
        btns.addWidget(btn_cancel)
        form.addRow(btns)

        if dlg.exec() == QDialog.DialogCode.Accepted:
            from_id = from_combo.currentData()
            to_id = to_combo.currentData()
            amount = amount_spin.value()
            if from_id == to_id:
                QMessageBox.warning(self, "خطأ", "لا يمكن التحويل لنفس الخزنة")
                return
            if amount <= 0:
                QMessageBox.warning(self, "خطأ", "المبلغ يجب أن يكون أكبر من صفر")
                return
            try:
                db.transfer_between_vaults(from_id, to_id, amount, desc_edit.text().strip())
                self.refresh_all()
                QMessageBox.information(self, "تم", "تم التحويل بنجاح")
            except Exception as e:
                QMessageBox.critical(self, "خطأ", str(e))

    def _adjust_dialog(self):
        vaults = db.get_all_vaults()
        if not vaults:
            return

        dlg = QDialog(self)
        dlg.setWindowTitle("تعديل رصيد خزنة")
        dlg.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        dlg.setMinimumWidth(400)
        form = QFormLayout(dlg)

        vault_combo = QComboBox()
        for v in vaults:
            vault_combo.addItem(f"{v['name']} ({format_currency(v['balance'])})", v["id"])
        form.addRow("الخزنة:", vault_combo)

        amount_spin = QDoubleSpinBox()
        amount_spin.setMinimum(-99999999)
        amount_spin.setMaximum(99999999)
        amount_spin.setDecimals(2)
        form.addRow("المبلغ (+ أو -):", amount_spin)

        desc_edit = QLineEdit()
        desc_edit.setPlaceholderText("سبب التعديل")
        form.addRow("الوصف:", desc_edit)

        btns = QHBoxLayout()
        btn_ok = QPushButton("تعديل")
        btn_ok.clicked.connect(dlg.accept)
        btn_cancel = QPushButton("إلغاء")
        btn_cancel.setObjectName("btn_secondary")
        btn_cancel.clicked.connect(dlg.reject)
        btns.addWidget(btn_ok)
        btns.addWidget(btn_cancel)
        form.addRow(btns)

        if dlg.exec() == QDialog.DialogCode.Accepted:
            vault_id = vault_combo.currentData()
            amount = amount_spin.value()
            if amount == 0:
                return
            reply = QMessageBox.question(
                self, "تأكيد",
                f"هل أنت متأكد من تعديل الرصيد بمبلغ {format_currency(amount)}؟",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                try:
                    db.adjust_vault(vault_id, amount, desc_edit.text().strip())
                    self.refresh_all()
                except Exception as e:
                    QMessageBox.critical(self, "خطأ", str(e))
