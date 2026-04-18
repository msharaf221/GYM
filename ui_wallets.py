"""
ui_wallets.py - Digital Wallet & Remittance Management UI
Handles: wallet registry, monthly limit tracking, transaction recording, commission logic.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QTableWidget, QTableWidgetItem, QDialog, QFormLayout, QDoubleSpinBox,
    QComboBox, QMessageBox, QHeaderView, QProgressBar, QFrame, QGridLayout,
)
from PyQt6.QtCore import Qt

import database as db
from utils import format_currency, generate_wallet_receipt, save_receipt_to_file


class WalletsPage(QWidget):
    """Main digital wallet management page."""

    def __init__(self, user_role="admin"):
        super().__init__()
        self.user_role = user_role
        self._setup_ui()
        self.refresh_all()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Header
        header = QHBoxLayout()
        title = QLabel("المحافظ الرقمية والتحويلات")
        title.setObjectName("section_title")
        header.addWidget(title)
        header.addStretch()

        btn_add_wallet = QPushButton("+ إضافة محفظة")
        btn_add_wallet.clicked.connect(self._add_wallet)
        header.addWidget(btn_add_wallet)

        btn_new_txn = QPushButton("+ معاملة جديدة")
        btn_new_txn.setObjectName("btn_success")
        btn_new_txn.clicked.connect(self._new_transaction)
        header.addWidget(btn_new_txn)

        layout.addLayout(header)

        # Wallet cards area
        self.cards_frame = QFrame()
        self.cards_layout = QGridLayout(self.cards_frame)
        self.cards_layout.setSpacing(12)
        layout.addWidget(self.cards_frame)

        # Transactions table
        lbl_txns = QLabel("سجل المعاملات")
        lbl_txns.setObjectName("section_title")
        layout.addWidget(lbl_txns)

        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)

        columns = ["ID", "المحفظة", "النوع", "المبلغ", "رقم العميل",
                    "رسوم النظام", "عمولة المحل", "التاريخ"]
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels(columns)
        self.table.setColumnHidden(0, True)

        hdr = self.table.horizontalHeader()
        for i in range(1, len(columns)):
            hdr.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)

        layout.addWidget(self.table)

    def refresh_all(self):
        self._refresh_wallet_cards()
        self._refresh_transactions()

    def _refresh_wallet_cards(self):
        # Clear existing cards
        while self.cards_layout.count():
            child = self.cards_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        wallets = db.get_all_wallets()
        for idx, wallet in enumerate(wallets):
            card = self._create_wallet_card(wallet)
            row = idx // 3
            col = idx % 3
            self.cards_layout.addWidget(card, row, col)

    def _create_wallet_card(self, wallet):
        card = QFrame()
        card.setObjectName("stat_card")
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(8)

        # Wallet name & provider
        name_lbl = QLabel(f"{wallet['name']} ({wallet['provider']})")
        name_lbl.setObjectName("stat_value")
        name_lbl.setStyleSheet("font-size: 16px;")
        card_layout.addWidget(name_lbl)

        phone_lbl = QLabel(f"الرقم: {wallet['phone_number']}")
        phone_lbl.setObjectName("subtitle")
        card_layout.addWidget(phone_lbl)

        balance_lbl = QLabel(f"الرصيد: {format_currency(wallet['balance'])}")
        card_layout.addWidget(balance_lbl)

        # Monthly limit progress
        monthly_usage = db.get_wallet_monthly_usage(wallet["id"])
        limit = wallet["monthly_limit"]
        pct = min(100, (monthly_usage / limit * 100)) if limit > 0 else 0

        progress = QProgressBar()
        progress.setMaximum(100)
        progress.setValue(int(pct))
        progress.setFormat(f"{format_currency(monthly_usage)} / {format_currency(limit)} ({pct:.0f}%)")

        if pct >= 90:
            progress.setProperty("danger", True)
        elif pct >= 80:
            progress.setProperty("warning", True)
        progress.style().unpolish(progress)
        progress.style().polish(progress)

        card_layout.addWidget(progress)

        if pct >= 80:
            warn = QLabel("تحذير: اقتراب من الحد الشهري!")
            warn.setStyleSheet("color: #e94560; font-weight: bold;")
            card_layout.addWidget(warn)

        # Action buttons
        btns = QHBoxLayout()
        btn_edit = QPushButton("تعديل")
        btn_edit.setObjectName("btn_secondary")
        btn_edit.setFixedWidth(60)
        btn_edit.clicked.connect(lambda _, wid=wallet["id"]: self._edit_wallet(wid))
        btns.addWidget(btn_edit)

        if self.user_role == "admin":
            btn_del = QPushButton("حذف")
            btn_del.setObjectName("btn_danger")
            btn_del.setFixedWidth(60)
            btn_del.clicked.connect(lambda _, wid=wallet["id"]: self._delete_wallet(wid))
            btns.addWidget(btn_del)

        card_layout.addLayout(btns)
        return card

    def _refresh_transactions(self):
        txns = db.get_wallet_transactions()
        type_map = {"deposit": "إيداع", "withdraw": "سحب", "transfer": "تحويل"}
        self.table.setRowCount(len(txns))
        for row, txn in enumerate(txns):
            self.table.setItem(row, 0, QTableWidgetItem(txn["id"]))
            self.table.setItem(row, 1, QTableWidgetItem(txn["wallet_name"]))
            self.table.setItem(row, 2, QTableWidgetItem(type_map.get(txn["transaction_type"], txn["transaction_type"])))
            self.table.setItem(row, 3, QTableWidgetItem(format_currency(txn["amount"])))
            self.table.setItem(row, 4, QTableWidgetItem(txn["client_phone"] or ""))
            self.table.setItem(row, 5, QTableWidgetItem(format_currency(txn["system_fee"])))
            self.table.setItem(row, 6, QTableWidgetItem(format_currency(txn["shop_commission"])))
            self.table.setItem(row, 7, QTableWidgetItem(txn["created_at"] or ""))

    def _add_wallet(self):
        dlg = WalletDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            try:
                db.add_wallet(**data)
                self.refresh_all()
            except Exception as e:
                QMessageBox.critical(self, "خطأ", str(e))

    def _edit_wallet(self, w_id):
        wallets = db.get_all_wallets()
        wallet = None
        for w in wallets:
            if w["id"] == w_id:
                wallet = w
                break
        if not wallet:
            return
        dlg = WalletDialog(self, wallet)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            try:
                db.update_wallet(w_id, data["name"], data["provider"],
                                 data["phone_number"], data["monthly_limit"])
                self.refresh_all()
            except Exception as e:
                QMessageBox.critical(self, "خطأ", str(e))

    def _delete_wallet(self, w_id):
        reply = QMessageBox.question(
            self, "تأكيد الحذف",
            "هل أنت متأكد من حذف هذه المحفظة وجميع معاملاتها؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            db.delete_wallet(w_id)
            self.refresh_all()

    def _new_transaction(self):
        wallets = db.get_all_wallets()
        if not wallets:
            QMessageBox.warning(self, "تنبيه", "يجب إضافة محفظة أولاً")
            return
        dlg = WalletTransactionDialog(self, wallets)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            try:
                # Check monthly limit
                usage = db.get_wallet_monthly_usage(data["wallet_id"])
                wallet = None
                for w in wallets:
                    if w["id"] == data["wallet_id"]:
                        wallet = w
                        break
                if wallet and (usage + data["amount"]) > wallet["monthly_limit"]:
                    reply = QMessageBox.warning(
                        self, "تجاوز الحد",
                        f"هذه المعاملة ستتجاوز الحد الشهري ({format_currency(wallet['monthly_limit'])})\n"
                        f"الاستخدام الحالي: {format_currency(usage)}\n"
                        "هل تريد المتابعة؟",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    )
                    if reply != QMessageBox.StandardButton.Yes:
                        return

                t_id = db.add_wallet_transaction(**data)
                self.refresh_all()

                # Receipt
                wallet_name = wallet["name"] if wallet else ""
                receipt = generate_wallet_receipt(
                    wallet_name, data["transaction_type"], data["amount"],
                    data["client_phone"], data["system_fee"], data["shop_commission"], t_id,
                )
                reply = QMessageBox.question(
                    self, "تمت المعاملة",
                    f"تمت المعاملة بنجاح\n\nهل تريد حفظ الإيصال؟",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                )
                if reply == QMessageBox.StandardButton.Yes:
                    path = save_receipt_to_file(receipt, f"wallet_{t_id}.txt")
                    QMessageBox.information(self, "تم", f"تم حفظ الإيصال:\n{path}")
            except Exception as e:
                QMessageBox.critical(self, "خطأ", str(e))


class WalletDialog(QDialog):
    """Add / Edit wallet dialog."""

    def __init__(self, parent=None, wallet=None):
        super().__init__(parent)
        self.wallet = wallet
        self.setWindowTitle("تعديل محفظة" if wallet else "إضافة محفظة جديدة")
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setMinimumWidth(400)
        self._setup_ui()

    def _setup_ui(self):
        form = QFormLayout(self)
        form.setSpacing(12)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("مثال: فودافون كاش - محمد")
        form.addRow("اسم المحفظة:", self.name_edit)

        self.provider_combo = QComboBox()
        self.provider_combo.setEditable(True)
        self.provider_combo.addItems([
            "Vodafone Cash", "InstaPay", "Orange Money",
            "Etisalat Cash", "Fawry", "WE Pay", "أخرى",
        ])
        form.addRow("المزود:", self.provider_combo)

        self.phone_edit = QLineEdit()
        self.phone_edit.setPlaceholderText("رقم المحفظة")
        form.addRow("رقم الهاتف:", self.phone_edit)

        self.limit_spin = QDoubleSpinBox()
        self.limit_spin.setMaximum(99999999)
        self.limit_spin.setDecimals(0)
        self.limit_spin.setValue(200000)
        form.addRow("الحد الشهري:", self.limit_spin)

        if not self.wallet:
            self.balance_spin = QDoubleSpinBox()
            self.balance_spin.setMaximum(99999999)
            self.balance_spin.setDecimals(2)
            form.addRow("الرصيد الافتتاحي:", self.balance_spin)

        if self.wallet:
            self.name_edit.setText(self.wallet["name"])
            self.provider_combo.setCurrentText(self.wallet["provider"])
            self.phone_edit.setText(self.wallet["phone_number"] or "")
            self.limit_spin.setValue(self.wallet["monthly_limit"])

        btns = QHBoxLayout()
        btn_save = QPushButton("حفظ")
        btn_save.clicked.connect(self._validate_and_accept)
        btn_cancel = QPushButton("إلغاء")
        btn_cancel.setObjectName("btn_secondary")
        btn_cancel.clicked.connect(self.reject)
        btns.addWidget(btn_save)
        btns.addWidget(btn_cancel)
        form.addRow(btns)

    def _validate_and_accept(self):
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "تنبيه", "اسم المحفظة مطلوب")
            return
        self.accept()

    def get_data(self):
        data = {
            "name": self.name_edit.text().strip(),
            "provider": self.provider_combo.currentText(),
            "phone_number": self.phone_edit.text().strip(),
            "monthly_limit": self.limit_spin.value(),
        }
        if not self.wallet:
            data["balance"] = self.balance_spin.value()
        return data


class WalletTransactionDialog(QDialog):
    """Record a wallet transaction dialog."""

    def __init__(self, parent=None, wallets=None):
        super().__init__(parent)
        self.wallets = wallets or []
        self.setWindowTitle("معاملة محفظة جديدة")
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setMinimumWidth(450)
        self._setup_ui()

    def _setup_ui(self):
        form = QFormLayout(self)
        form.setSpacing(12)

        self.wallet_combo = QComboBox()
        for w in self.wallets:
            usage = db.get_wallet_monthly_usage(w["id"])
            pct = (usage / w["monthly_limit"] * 100) if w["monthly_limit"] > 0 else 0
            self.wallet_combo.addItem(
                f"{w['name']} - {w['provider']} ({pct:.0f}% مستخدم)", w["id"]
            )
        form.addRow("المحفظة:", self.wallet_combo)

        self.type_combo = QComboBox()
        self.type_combo.addItem("إيداع", "deposit")
        self.type_combo.addItem("سحب", "withdraw")
        self.type_combo.addItem("تحويل", "transfer")
        form.addRow("نوع المعاملة:", self.type_combo)

        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setMaximum(99999999)
        self.amount_spin.setDecimals(2)
        form.addRow("المبلغ:", self.amount_spin)

        self.client_phone = QLineEdit()
        self.client_phone.setPlaceholderText("رقم هاتف العميل")
        form.addRow("رقم العميل:", self.client_phone)

        self.system_fee = QDoubleSpinBox()
        self.system_fee.setMaximum(99999)
        self.system_fee.setDecimals(2)
        form.addRow("رسوم النظام:", self.system_fee)

        self.commission = QDoubleSpinBox()
        self.commission.setMaximum(99999)
        self.commission.setDecimals(2)
        form.addRow("عمولة المحل:", self.commission)

        self.notes_edit = QLineEdit()
        self.notes_edit.setPlaceholderText("ملاحظات (اختياري)")
        form.addRow("ملاحظات:", self.notes_edit)

        # Vault for commission
        self.vault_combo = QComboBox()
        self.vault_combo.addItem("-- بدون تسجيل عمولة في خزنة --", None)
        vaults = db.get_all_vaults()
        for v in vaults:
            self.vault_combo.addItem(v["name"], v["id"])
        form.addRow("خزنة العمولة:", self.vault_combo)

        btns = QHBoxLayout()
        btn_save = QPushButton("تسجيل المعاملة")
        btn_save.setObjectName("btn_success")
        btn_save.clicked.connect(self._validate_and_accept)
        btn_cancel = QPushButton("إلغاء")
        btn_cancel.setObjectName("btn_secondary")
        btn_cancel.clicked.connect(self.reject)
        btns.addWidget(btn_save)
        btns.addWidget(btn_cancel)
        form.addRow(btns)

    def _validate_and_accept(self):
        if self.amount_spin.value() <= 0:
            QMessageBox.warning(self, "تنبيه", "المبلغ يجب أن يكون أكبر من صفر")
            return
        self.accept()

    def get_data(self):
        return {
            "wallet_id": self.wallet_combo.currentData(),
            "transaction_type": self.type_combo.currentData(),
            "amount": self.amount_spin.value(),
            "client_phone": self.client_phone.text().strip(),
            "system_fee": self.system_fee.value(),
            "shop_commission": self.commission.value(),
            "notes": self.notes_edit.text().strip(),
            "vault_id": self.vault_combo.currentData(),
        }
