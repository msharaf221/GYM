"""
ui_maintenance.py - Maintenance (Repairs) Hub UI
Handles: repair lifecycle, spare part cost tracking, profit calculation, status management.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QTableWidget, QTableWidgetItem, QDialog, QFormLayout, QDoubleSpinBox,
    QComboBox, QMessageBox, QHeaderView, QTextEdit,
)
from PyQt6.QtCore import Qt

import database as db
from utils import format_currency, generate_maintenance_receipt, save_receipt_to_file

STATUS_MAP = {
    "received": "مستلم",
    "in_progress": "قيد العمل",
    "ready": "جاهز",
    "delivered": "تم التسليم",
}

STATUS_COLORS = {
    "received": "#3498db",
    "in_progress": "#f39c12",
    "ready": "#27ae60",
    "delivered": "#95a5a6",
}


class MaintenancePage(QWidget):
    """Main maintenance management page."""

    def __init__(self, user_role="admin"):
        super().__init__()
        self.user_role = user_role
        self._setup_ui()
        self.refresh_table()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Header
        header = QHBoxLayout()
        title = QLabel("مركز الصيانة")
        title.setObjectName("section_title")
        header.addWidget(title)
        header.addStretch()

        btn_add = QPushButton("+ طلب صيانة جديد")
        btn_add.clicked.connect(self._add_repair)
        header.addWidget(btn_add)
        layout.addLayout(header)

        # Status filter
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("تصفية:"))

        self.filter_combo = QComboBox()
        self.filter_combo.addItem("الكل", "all")
        for key, val in STATUS_MAP.items():
            self.filter_combo.addItem(val, key)
        self.filter_combo.currentIndexChanged.connect(self._on_filter)
        filter_layout.addWidget(self.filter_combo)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("بحث بالاسم أو الهاتف أو الجهاز...")
        self.search_input.textChanged.connect(self._on_search)
        filter_layout.addWidget(self.search_input)
        layout.addLayout(filter_layout)

        # Table
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)

        columns = ["ID", "العميل", "الهاتف", "الجهاز", "المشكلة",
                    "الحالة", "قطع غيار", "رسوم الخدمة", "صافي الربح", "إجراءات"]
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels(columns)
        self.table.setColumnHidden(0, True)

        hdr = self.table.horizontalHeader()
        for i in range(1, len(columns) - 1):
            hdr.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(len(columns) - 1, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(len(columns) - 1, 320)

        layout.addWidget(self.table)

    def refresh_table(self):
        items = db.get_all_maintenance()
        self._populate_table(items)

    def _populate_table(self, items):
        self.table.setRowCount(len(items))
        for row, item in enumerate(items):
            self.table.setItem(row, 0, QTableWidgetItem(item["id"]))
            self.table.setItem(row, 1, QTableWidgetItem(item["customer_name"]))
            self.table.setItem(row, 2, QTableWidgetItem(item["phone"] or ""))
            self.table.setItem(row, 3, QTableWidgetItem(item["device_type"]))
            self.table.setItem(row, 4, QTableWidgetItem(item["issue_description"]))

            status_text = STATUS_MAP.get(item["status"], item["status"])
            status_item = QTableWidgetItem(status_text)
            self.table.setItem(row, 5, status_item)

            self.table.setItem(row, 6, QTableWidgetItem(format_currency(item["spare_part_cost"])))
            self.table.setItem(row, 7, QTableWidgetItem(format_currency(item["service_fee"])))

            net = item["service_fee"] - item["spare_part_cost"]
            profit_item = QTableWidgetItem(format_currency(net))
            self.table.setItem(row, 8, profit_item)

            # Actions
            actions = QWidget()
            actions_layout = QHBoxLayout(actions)
            actions_layout.setContentsMargins(4, 4, 4, 4)
            actions_layout.setSpacing(4)

            if item["status"] != "delivered":
                btn_next = QPushButton("تقدم")
                btn_next.setObjectName("btn_success")
                btn_next.setFixedWidth(55)
                btn_next.clicked.connect(lambda _, mid=item["id"], s=item["status"]: self._advance_status(mid, s))
                actions_layout.addWidget(btn_next)

            btn_edit = QPushButton("تعديل")
            btn_edit.setObjectName("btn_secondary")
            btn_edit.setFixedWidth(55)
            btn_edit.clicked.connect(lambda _, mid=item["id"]: self._edit_repair(mid))
            actions_layout.addWidget(btn_edit)

            btn_receipt = QPushButton("إيصال")
            btn_receipt.setObjectName("btn_secondary")
            btn_receipt.setFixedWidth(55)
            btn_receipt.clicked.connect(lambda _, mid=item["id"]: self._print_receipt(mid))
            actions_layout.addWidget(btn_receipt)

            if self.user_role == "admin":
                btn_del = QPushButton("حذف")
                btn_del.setObjectName("btn_danger")
                btn_del.setFixedWidth(55)
                btn_del.clicked.connect(lambda _, mid=item["id"]: self._delete_repair(mid))
                actions_layout.addWidget(btn_del)

            self.table.setCellWidget(row, 9, actions)

    def _on_filter(self):
        status = self.filter_combo.currentData()
        if status == "all":
            items = db.get_all_maintenance()
        else:
            items = db.get_maintenance_by_status(status)
        self._populate_table(items)

    def _on_search(self, text):
        if text.strip():
            items = db.search_maintenance(text.strip())
        else:
            items = db.get_all_maintenance()
        self._populate_table(items)

    def _add_repair(self):
        dlg = MaintenanceDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            try:
                db.add_maintenance(**data)
                self.refresh_table()
            except Exception as e:
                QMessageBox.critical(self, "خطأ", str(e))

    def _edit_repair(self, m_id):
        items = db.get_all_maintenance()
        item = None
        for i in items:
            if i["id"] == m_id:
                item = i
                break
        if not item:
            return
        dlg = MaintenanceDialog(self, item)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            try:
                db.update_maintenance(m_id, data["customer_name"], data["phone"],
                                      data["device_type"], data["issue_description"],
                                      data["spare_part_cost"], data["service_fee"], data["notes"])
                self.refresh_table()
            except Exception as e:
                QMessageBox.critical(self, "خطأ", str(e))

    def _advance_status(self, m_id, current_status):
        order = ["received", "in_progress", "ready", "delivered"]
        idx = order.index(current_status)
        if idx >= len(order) - 1:
            return
        next_status = order[idx + 1]
        next_label = STATUS_MAP[next_status]

        vault_id = None
        if next_status == "delivered":
            # Select vault for revenue
            vaults = db.get_all_vaults()
            if vaults:
                vault_id = vaults[0]["id"]  # Default to cash
                dlg = QDialog(self)
                dlg.setWindowTitle("اختر الخزنة")
                dlg.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
                form = QFormLayout(dlg)
                combo = QComboBox()
                for v in vaults:
                    combo.addItem(v["name"], v["id"])
                form.addRow("الخزنة:", combo)
                btns = QHBoxLayout()
                btn_ok = QPushButton("تأكيد")
                btn_ok.clicked.connect(dlg.accept)
                btn_cancel = QPushButton("إلغاء")
                btn_cancel.setObjectName("btn_secondary")
                btn_cancel.clicked.connect(dlg.reject)
                btns.addWidget(btn_ok)
                btns.addWidget(btn_cancel)
                form.addRow(btns)
                if dlg.exec() != QDialog.DialogCode.Accepted:
                    return
                vault_id = combo.currentData()

        reply = QMessageBox.question(
            self, "تأكيد",
            f"هل تريد تغيير الحالة إلى: {next_label}؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            db.update_maintenance_status(m_id, next_status, vault_id)
            self.refresh_table()

    def _delete_repair(self, m_id):
        reply = QMessageBox.question(
            self, "تأكيد الحذف", "هل أنت متأكد من حذف هذا الطلب؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            db.delete_maintenance(m_id)
            self.refresh_table()

    def _print_receipt(self, m_id):
        items = db.get_all_maintenance()
        item = None
        for i in items:
            if i["id"] == m_id:
                item = i
                break
        if not item:
            return
        receipt = generate_maintenance_receipt(
            item["customer_name"], item["device_type"], item["issue_description"],
            item["service_fee"], item["spare_part_cost"], m_id,
        )
        reply = QMessageBox.question(
            self, "إيصال",
            f"{receipt}\n\nهل تريد حفظ الإيصال؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            path = save_receipt_to_file(receipt, f"maintenance_{m_id}.txt")
            QMessageBox.information(self, "تم", f"تم حفظ الإيصال:\n{path}")


class MaintenanceDialog(QDialog):
    """Add / Edit maintenance record dialog."""

    def __init__(self, parent=None, item=None):
        super().__init__(parent)
        self.item = item
        self.setWindowTitle("تعديل طلب صيانة" if item else "طلب صيانة جديد")
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setMinimumWidth(500)
        self._setup_ui()

    def _setup_ui(self):
        form = QFormLayout(self)
        form.setSpacing(12)

        self.customer_name = QLineEdit()
        self.customer_name.setPlaceholderText("اسم العميل *")
        form.addRow("العميل:", self.customer_name)

        self.phone = QLineEdit()
        self.phone.setPlaceholderText("رقم الهاتف")
        form.addRow("الهاتف:", self.phone)

        self.device_type = QLineEdit()
        self.device_type.setPlaceholderText("مثال: iPhone 15, Samsung S24 *")
        form.addRow("الجهاز:", self.device_type)

        self.issue = QTextEdit()
        self.issue.setPlaceholderText("وصف المشكلة *")
        self.issue.setMaximumHeight(80)
        form.addRow("المشكلة:", self.issue)

        self.spare_cost = QDoubleSpinBox()
        self.spare_cost.setMaximum(999999)
        self.spare_cost.setDecimals(2)
        form.addRow("تكلفة قطع الغيار:", self.spare_cost)

        self.service_fee = QDoubleSpinBox()
        self.service_fee.setMaximum(999999)
        self.service_fee.setDecimals(2)
        form.addRow("رسوم الخدمة:", self.service_fee)

        # Link spare part from inventory
        self.spare_combo = QComboBox()
        self.spare_combo.addItem("-- بدون ربط بالمخزون --", None)
        inventory = db.get_all_inventory()
        for inv in inventory:
            if inv["quantity"] > 0:
                self.spare_combo.addItem(
                    f"{inv['name']} (متاح: {inv['quantity']})", inv["id"]
                )
        form.addRow("قطعة من المخزون:", self.spare_combo)

        self.notes = QTextEdit()
        self.notes.setPlaceholderText("ملاحظات إضافية")
        self.notes.setMaximumHeight(60)
        form.addRow("ملاحظات:", self.notes)

        # Populate if editing
        if self.item:
            self.customer_name.setText(self.item["customer_name"])
            self.phone.setText(self.item["phone"] or "")
            self.device_type.setText(self.item["device_type"])
            self.issue.setPlainText(self.item["issue_description"])
            self.spare_cost.setValue(self.item["spare_part_cost"])
            self.service_fee.setValue(self.item["service_fee"])
            self.notes.setPlainText(self.item["notes"] or "")

        # Buttons
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
        if not self.customer_name.text().strip():
            QMessageBox.warning(self, "تنبيه", "اسم العميل مطلوب")
            return
        if not self.device_type.text().strip():
            QMessageBox.warning(self, "تنبيه", "نوع الجهاز مطلوب")
            return
        if not self.issue.toPlainText().strip():
            QMessageBox.warning(self, "تنبيه", "وصف المشكلة مطلوب")
            return
        self.accept()

    def get_data(self):
        return {
            "customer_name": self.customer_name.text().strip(),
            "phone": self.phone.text().strip(),
            "device_type": self.device_type.text().strip(),
            "issue_description": self.issue.toPlainText().strip(),
            "spare_part_cost": self.spare_cost.value(),
            "service_fee": self.service_fee.value(),
            "spare_part_inventory_id": self.spare_combo.currentData(),
            "notes": self.notes.toPlainText().strip(),
        }
