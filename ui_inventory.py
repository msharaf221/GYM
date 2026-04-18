"""
ui_inventory.py - Inventory (Accessories) Management UI
Handles: CRUD, barcode/SKU, stock tracking, sales, low stock alerts, price updates.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QTableWidget, QTableWidgetItem, QDialog, QFormLayout, QDoubleSpinBox,
    QSpinBox, QComboBox, QMessageBox, QHeaderView, QFrame, QTextEdit,
    QFileDialog,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon

import database as db
from utils import format_currency, generate_sale_receipt, save_receipt_to_file


class InventoryPage(QWidget):
    """Main inventory management page."""

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
        title = QLabel("إدارة المخزون (الإكسسوارات)")
        title.setObjectName("section_title")
        header.addWidget(title)
        header.addStretch()

        btn_low_stock = QPushButton("⚠ تنبيهات المخزون")
        btn_low_stock.setObjectName("btn_secondary")
        btn_low_stock.clicked.connect(self._show_low_stock)
        header.addWidget(btn_low_stock)

        btn_add = QPushButton("+ إضافة منتج")
        btn_add.clicked.connect(self._add_item)
        header.addWidget(btn_add)

        layout.addLayout(header)

        # Search bar
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("بحث بالاسم أو الكود أو الباركود...")
        self.search_input.textChanged.connect(self._on_search)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)

        # Table
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)

        columns = ["ID", "الاسم", "الكود", "الباركود", "التصنيف",
                    "سعر الشراء", "سعر البيع", "الكمية", "الحد الأدنى", "إجراءات"]
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels(columns)
        self.table.setColumnHidden(0, True)  # Hide ID

        hdr = self.table.horizontalHeader()
        for i in range(1, len(columns) - 1):
            hdr.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(len(columns) - 1, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(len(columns) - 1, 300)

        layout.addWidget(self.table)

    def refresh_table(self):
        items = db.get_all_inventory()
        self._populate_table(items)

    def _populate_table(self, items):
        self.table.setRowCount(len(items))
        for row, item in enumerate(items):
            self.table.setItem(row, 0, QTableWidgetItem(item["id"]))
            self.table.setItem(row, 1, QTableWidgetItem(item["name"]))
            self.table.setItem(row, 2, QTableWidgetItem(item["code"] or ""))
            self.table.setItem(row, 3, QTableWidgetItem(item["barcode"] or ""))
            self.table.setItem(row, 4, QTableWidgetItem(item["category"] or ""))
            self.table.setItem(row, 5, QTableWidgetItem(format_currency(item["buy_price"])))
            self.table.setItem(row, 6, QTableWidgetItem(format_currency(item["sell_price"])))

            qty_item = QTableWidgetItem(str(item["quantity"]))
            if item["quantity"] <= item["low_stock_threshold"]:
                qty_item.setForeground(Qt.GlobalColor.red)
            self.table.setItem(row, 7, qty_item)
            self.table.setItem(row, 8, QTableWidgetItem(str(item["low_stock_threshold"])))

            # Action buttons
            actions = QWidget()
            actions_layout = QHBoxLayout(actions)
            actions_layout.setContentsMargins(4, 4, 4, 4)
            actions_layout.setSpacing(4)

            btn_sell = QPushButton("بيع")
            btn_sell.setObjectName("btn_success")
            btn_sell.setFixedWidth(55)
            btn_sell.clicked.connect(lambda _, iid=item["id"]: self._sell_item(iid))
            actions_layout.addWidget(btn_sell)

            btn_price = QPushButton("سعر")
            btn_price.setObjectName("btn_secondary")
            btn_price.setFixedWidth(55)
            btn_price.clicked.connect(lambda _, iid=item["id"]: self._quick_price(iid))
            actions_layout.addWidget(btn_price)

            btn_edit = QPushButton("تعديل")
            btn_edit.setObjectName("btn_secondary")
            btn_edit.setFixedWidth(55)
            btn_edit.clicked.connect(lambda _, iid=item["id"]: self._edit_item(iid))
            actions_layout.addWidget(btn_edit)

            if self.user_role == "admin":
                btn_del = QPushButton("حذف")
                btn_del.setObjectName("btn_danger")
                btn_del.setFixedWidth(55)
                btn_del.clicked.connect(lambda _, iid=item["id"]: self._delete_item(iid))
                actions_layout.addWidget(btn_del)

            self.table.setCellWidget(row, 9, actions)

    def _on_search(self, text):
        if text.strip():
            items = db.search_inventory(text.strip())
        else:
            items = db.get_all_inventory()
        self._populate_table(items)

    def _add_item(self):
        dlg = InventoryDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            try:
                db.add_inventory_item(**data)
                self.refresh_table()
            except Exception as e:
                QMessageBox.critical(self, "خطأ", str(e))

    def _edit_item(self, item_id):
        item = db.get_inventory_item(item_id)
        if not item:
            return
        dlg = InventoryDialog(self, item)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            try:
                db.update_inventory_item(item_id, **data)
                self.refresh_table()
            except Exception as e:
                QMessageBox.critical(self, "خطأ", str(e))

    def _delete_item(self, item_id):
        reply = QMessageBox.question(
            self, "تأكيد الحذف", "هل أنت متأكد من حذف هذا المنتج؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            db.delete_inventory_item(item_id)
            self.refresh_table()

    def _sell_item(self, item_id):
        item = db.get_inventory_item(item_id)
        if not item:
            return
        dlg = SaleDialog(self, item)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            try:
                sale_id, profit = db.record_sale(
                    item_id, data["quantity"], data["sell_price"],
                    item["buy_price"], data["vault_id"],
                )
                self.refresh_table()
                # Receipt
                receipt = generate_sale_receipt(
                    item["name"], data["quantity"], data["sell_price"],
                    data["quantity"] * data["sell_price"], sale_id,
                )
                reply = QMessageBox.question(
                    self, "تم البيع بنجاح",
                    f"تم البيع بنجاح\nالربح: {format_currency(profit)}\n\nهل تريد حفظ الإيصال؟",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                )
                if reply == QMessageBox.StandardButton.Yes:
                    path = save_receipt_to_file(receipt, f"sale_{sale_id}.txt")
                    QMessageBox.information(self, "تم", f"تم حفظ الإيصال:\n{path}")
            except ValueError as e:
                QMessageBox.warning(self, "تنبيه", str(e))

    def _quick_price(self, item_id):
        item = db.get_inventory_item(item_id)
        if not item:
            return
        dlg = QDialog(self)
        dlg.setWindowTitle("تحديث سعر سريع")
        dlg.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        dlg.setMinimumWidth(300)
        form = QFormLayout(dlg)

        lbl = QLabel(f"المنتج: {item['name']}")
        form.addRow(lbl)

        price_spin = QDoubleSpinBox()
        price_spin.setMaximum(999999)
        price_spin.setDecimals(2)
        price_spin.setValue(item["sell_price"])
        form.addRow("سعر البيع الجديد:", price_spin)

        btns = QHBoxLayout()
        btn_ok = QPushButton("حفظ")
        btn_ok.clicked.connect(dlg.accept)
        btn_cancel = QPushButton("إلغاء")
        btn_cancel.setObjectName("btn_secondary")
        btn_cancel.clicked.connect(dlg.reject)
        btns.addWidget(btn_ok)
        btns.addWidget(btn_cancel)
        form.addRow(btns)

        if dlg.exec() == QDialog.DialogCode.Accepted:
            db.quick_update_price(item_id, price_spin.value())
            self.refresh_table()

    def _show_low_stock(self):
        items = db.get_low_stock_items()
        if not items:
            QMessageBox.information(self, "المخزون", "لا توجد منتجات بمخزون منخفض")
            return
        dlg = QDialog(self)
        dlg.setWindowTitle("تنبيهات المخزون المنخفض")
        dlg.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        dlg.setMinimumSize(500, 400)
        layout = QVBoxLayout(dlg)
        lbl = QLabel(f"عدد المنتجات بمخزون منخفض: {len(items)}")
        lbl.setObjectName("section_title")
        layout.addWidget(lbl)

        tbl = QTableWidget()
        tbl.setColumnCount(4)
        tbl.setHorizontalHeaderLabels(["الاسم", "الكمية الحالية", "الحد الأدنى", "الحالة"])
        tbl.setRowCount(len(items))
        tbl.horizontalHeader().setStretchLastSection(True)
        for row, item in enumerate(items):
            tbl.setItem(row, 0, QTableWidgetItem(item["name"]))
            tbl.setItem(row, 1, QTableWidgetItem(str(item["quantity"])))
            tbl.setItem(row, 2, QTableWidgetItem(str(item["low_stock_threshold"])))
            status = "نفذ" if item["quantity"] == 0 else "منخفض"
            si = QTableWidgetItem(status)
            si.setForeground(Qt.GlobalColor.red)
            tbl.setItem(row, 3, si)
        layout.addWidget(tbl)

        btn_close = QPushButton("إغلاق")
        btn_close.setObjectName("btn_secondary")
        btn_close.clicked.connect(dlg.accept)
        layout.addWidget(btn_close)
        dlg.exec()


class InventoryDialog(QDialog):
    """Add / Edit inventory item dialog."""

    def __init__(self, parent=None, item=None):
        super().__init__(parent)
        self.item = item
        self.setWindowTitle("تعديل منتج" if item else "إضافة منتج جديد")
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setMinimumWidth(450)
        self._setup_ui()

    def _setup_ui(self):
        form = QFormLayout(self)
        form.setSpacing(12)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("اسم المنتج *")
        form.addRow("الاسم:", self.name_edit)

        self.code_edit = QLineEdit()
        self.code_edit.setPlaceholderText("تلقائي إذا فارغ")
        form.addRow("الكود:", self.code_edit)

        self.barcode_edit = QLineEdit()
        self.barcode_edit.setPlaceholderText("تلقائي إذا فارغ - أو امسح بالسكانر")
        form.addRow("الباركود:", self.barcode_edit)

        self.category_edit = QLineEdit()
        self.category_edit.setPlaceholderText("مثال: شواحن، سماعات، كفرات")
        form.addRow("التصنيف:", self.category_edit)

        self.buy_price = QDoubleSpinBox()
        self.buy_price.setMaximum(999999)
        self.buy_price.setDecimals(2)
        form.addRow("سعر الشراء:", self.buy_price)

        self.sell_price = QDoubleSpinBox()
        self.sell_price.setMaximum(999999)
        self.sell_price.setDecimals(2)
        form.addRow("سعر البيع:", self.sell_price)

        self.quantity = QSpinBox()
        self.quantity.setMaximum(999999)
        form.addRow("الكمية:", self.quantity)

        self.low_stock = QSpinBox()
        self.low_stock.setMaximum(99999)
        self.low_stock.setValue(5)
        form.addRow("حد التنبيه:", self.low_stock)

        # Populate if editing
        if self.item:
            self.name_edit.setText(self.item["name"])
            self.code_edit.setText(self.item["code"] or "")
            self.barcode_edit.setText(self.item["barcode"] or "")
            self.category_edit.setText(self.item["category"] or "")
            self.buy_price.setValue(self.item["buy_price"])
            self.sell_price.setValue(self.item["sell_price"])
            self.quantity.setValue(self.item["quantity"])
            self.low_stock.setValue(self.item["low_stock_threshold"])

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
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "تنبيه", "اسم المنتج مطلوب")
            return
        if self.sell_price.value() <= 0:
            QMessageBox.warning(self, "تنبيه", "سعر البيع يجب أن يكون أكبر من صفر")
            return
        self.accept()

    def get_data(self):
        return {
            "name": self.name_edit.text().strip(),
            "code": self.code_edit.text().strip(),
            "barcode": self.barcode_edit.text().strip(),
            "category": self.category_edit.text().strip(),
            "buy_price": self.buy_price.value(),
            "sell_price": self.sell_price.value(),
            "quantity": self.quantity.value(),
            "low_stock_threshold": self.low_stock.value(),
        }


class SaleDialog(QDialog):
    """Record a sale dialog."""

    def __init__(self, parent=None, item=None):
        super().__init__(parent)
        self.item = item
        self.setWindowTitle("تسجيل بيع")
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setMinimumWidth(400)
        self._setup_ui()

    def _setup_ui(self):
        form = QFormLayout(self)
        form.setSpacing(12)

        lbl = QLabel(f"المنتج: {self.item['name']}")
        lbl.setObjectName("section_title")
        form.addRow(lbl)

        avail = QLabel(f"المتاح: {self.item['quantity']}")
        avail.setObjectName("subtitle")
        form.addRow(avail)

        self.qty_spin = QSpinBox()
        self.qty_spin.setMinimum(1)
        self.qty_spin.setMaximum(self.item["quantity"])
        self.qty_spin.setValue(1)
        self.qty_spin.valueChanged.connect(self._update_total)
        form.addRow("الكمية:", self.qty_spin)

        self.price_spin = QDoubleSpinBox()
        self.price_spin.setMaximum(999999)
        self.price_spin.setDecimals(2)
        self.price_spin.setValue(self.item["sell_price"])
        self.price_spin.valueChanged.connect(self._update_total)
        form.addRow("سعر البيع:", self.price_spin)

        self.total_label = QLabel()
        form.addRow("الإجمالي:", self.total_label)

        self.profit_label = QLabel()
        form.addRow("الربح:", self.profit_label)

        # Vault selection
        self.vault_combo = QComboBox()
        vaults = db.get_all_vaults()
        for v in vaults:
            self.vault_combo.addItem(v["name"], v["id"])
        form.addRow("الخزنة:", self.vault_combo)

        self._update_total()

        btns = QHBoxLayout()
        btn_sell = QPushButton("تأكيد البيع")
        btn_sell.setObjectName("btn_success")
        btn_sell.clicked.connect(self.accept)
        btn_cancel = QPushButton("إلغاء")
        btn_cancel.setObjectName("btn_secondary")
        btn_cancel.clicked.connect(self.reject)
        btns.addWidget(btn_sell)
        btns.addWidget(btn_cancel)
        form.addRow(btns)

    def _update_total(self):
        qty = self.qty_spin.value()
        price = self.price_spin.value()
        total = qty * price
        profit = qty * (price - self.item["buy_price"])
        self.total_label.setText(format_currency(total))
        self.profit_label.setText(format_currency(profit))

    def get_data(self):
        return {
            "quantity": self.qty_spin.value(),
            "sell_price": self.price_spin.value(),
            "vault_id": self.vault_combo.currentData(),
        }
