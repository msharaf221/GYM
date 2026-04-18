"""
ui_sales.py - Dedicated Sales / Point-of-Sale Page
Handles: product search, cart, checkout, sale history, receipts.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QTableWidget, QTableWidgetItem, QDialog, QFormLayout, QDoubleSpinBox,
    QSpinBox, QComboBox, QMessageBox, QHeaderView, QFrame, QGridLayout,
    QSplitter, QDateEdit,
)
from PyQt6.QtCore import Qt, QDate

import database as db
from utils import format_currency, generate_sale_receipt, save_receipt_to_file


class SalesPage(QWidget):
    """Dedicated sales / POS page."""

    def __init__(self, user_role="admin"):
        super().__init__()
        self.user_role = user_role
        self.cart = []  # list of dicts: {item, quantity, sell_price}
        self._setup_ui()
        self._refresh_products()
        self._refresh_history()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        title = QLabel("نقطة البيع")
        title.setObjectName("section_title")
        layout.addWidget(title)

        # Main splitter: left = POS, right = history
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # ===== LEFT: POS Area =====
        pos_widget = QWidget()
        pos_layout = QVBoxLayout(pos_widget)
        pos_layout.setContentsMargins(0, 0, 10, 0)
        pos_layout.setSpacing(12)

        # Search bar
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("بحث بالاسم أو الكود أو الباركود...")
        self.search_input.textChanged.connect(self._on_search)
        search_layout.addWidget(self.search_input)
        pos_layout.addLayout(search_layout)

        # Products table
        prod_label = QLabel("المنتجات المتاحة")
        prod_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        pos_layout.addWidget(prod_label)

        self.products_table = QTableWidget()
        self.products_table.setAlternatingRowColors(True)
        self.products_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.products_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.products_table.horizontalHeader().setStretchLastSection(True)
        self.products_table.setColumnCount(6)
        self.products_table.setHorizontalHeaderLabels(
            ["ID", "الاسم", "الكود", "سعر البيع", "المتاح", "إضافة"]
        )
        self.products_table.setColumnHidden(0, True)
        hdr = self.products_table.horizontalHeader()
        for i in range(1, 5):
            hdr.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self.products_table.setColumnWidth(5, 100)
        pos_layout.addWidget(self.products_table)

        # Cart
        cart_label = QLabel("سلة المشتريات")
        cart_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #d4a017;")
        pos_layout.addWidget(cart_label)

        self.cart_table = QTableWidget()
        self.cart_table.setAlternatingRowColors(True)
        self.cart_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.cart_table.horizontalHeader().setStretchLastSection(True)
        self.cart_table.setColumnCount(6)
        self.cart_table.setHorizontalHeaderLabels(
            ["ID", "المنتج", "الكمية", "سعر الوحدة", "الإجمالي", "إزالة"]
        )
        self.cart_table.setColumnHidden(0, True)
        self.cart_table.setMaximumHeight(200)
        hdr2 = self.cart_table.horizontalHeader()
        for i in range(1, 5):
            hdr2.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
        hdr2.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self.cart_table.setColumnWidth(5, 80)
        pos_layout.addWidget(self.cart_table)

        # Totals and checkout
        totals_frame = QFrame()
        totals_frame.setObjectName("card")
        totals_layout = QHBoxLayout(totals_frame)

        self.total_label = QLabel("الإجمالي: 0.00 ج.م")
        self.total_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #d4a017;")
        totals_layout.addWidget(self.total_label)

        self.profit_label = QLabel("الربح: 0.00 ج.م")
        self.profit_label.setStyleSheet("font-size: 16px; color: #1a7a1a;")
        if self.user_role == "admin":
            totals_layout.addWidget(self.profit_label)

        totals_layout.addStretch()

        # Vault selection
        totals_layout.addWidget(QLabel("الخزنة:"))
        self.vault_combo = QComboBox()
        vaults = db.get_all_vaults()
        for v in vaults:
            self.vault_combo.addItem(v["name"], v["id"])
        self.vault_combo.setMinimumWidth(150)
        totals_layout.addWidget(self.vault_combo)

        btn_clear = QPushButton("مسح السلة")
        btn_clear.setObjectName("btn_secondary")
        btn_clear.clicked.connect(self._clear_cart)
        totals_layout.addWidget(btn_clear)

        btn_checkout = QPushButton("تأكيد البيع")
        btn_checkout.setObjectName("btn_success")
        btn_checkout.setMinimumWidth(120)
        btn_checkout.clicked.connect(self._checkout)
        totals_layout.addWidget(btn_checkout)

        pos_layout.addWidget(totals_frame)

        splitter.addWidget(pos_widget)

        # ===== RIGHT: Sale History =====
        history_widget = QWidget()
        history_layout = QVBoxLayout(history_widget)
        history_layout.setContentsMargins(10, 0, 0, 0)
        history_layout.setSpacing(12)

        hist_header = QHBoxLayout()
        hist_label = QLabel("سجل المبيعات")
        hist_label.setObjectName("section_title")
        hist_header.addWidget(hist_label)
        hist_header.addStretch()

        btn_refresh = QPushButton("تحديث")
        btn_refresh.setObjectName("btn_secondary")
        btn_refresh.clicked.connect(self._refresh_history)
        hist_header.addWidget(btn_refresh)
        history_layout.addLayout(hist_header)

        # Date filter
        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel("من:"))
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate.currentDate().addMonths(-1))
        date_layout.addWidget(self.date_from)
        date_layout.addWidget(QLabel("إلى:"))
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate())
        date_layout.addWidget(self.date_to)
        btn_filter = QPushButton("بحث")
        btn_filter.setObjectName("btn_secondary")
        btn_filter.clicked.connect(self._refresh_history)
        date_layout.addWidget(btn_filter)
        history_layout.addLayout(date_layout)

        self.history_table = QTableWidget()
        self.history_table.setAlternatingRowColors(True)
        self.history_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.history_table.horizontalHeader().setStretchLastSection(True)
        cols = ["المنتج", "الكمية", "سعر الوحدة", "الإجمالي", "الربح", "التاريخ"]
        self.history_table.setColumnCount(len(cols))
        self.history_table.setHorizontalHeaderLabels(cols)

        # Hide profit column for staff
        if self.user_role != "admin":
            self.history_table.setColumnHidden(4, True)

        hdr3 = self.history_table.horizontalHeader()
        for i in range(len(cols)):
            hdr3.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
        history_layout.addWidget(self.history_table)

        # Summary cards
        self.summary_frame = QFrame()
        self.summary_layout = QHBoxLayout(self.summary_frame)
        history_layout.addWidget(self.summary_frame)

        splitter.addWidget(history_widget)
        splitter.setSizes([600, 400])

        layout.addWidget(splitter)

    def _refresh_products(self):
        items = db.get_all_inventory()
        self._populate_products(items)

    def _populate_products(self, items):
        # Filter to items with stock > 0
        items = [i for i in items if i["quantity"] > 0]
        self.products_table.setRowCount(len(items))
        for row, item in enumerate(items):
            self.products_table.setItem(row, 0, QTableWidgetItem(item["id"]))
            self.products_table.setItem(row, 1, QTableWidgetItem(item["name"]))
            self.products_table.setItem(row, 2, QTableWidgetItem(item["code"] or ""))
            self.products_table.setItem(row, 3, QTableWidgetItem(format_currency(item["sell_price"])))
            qty_item = QTableWidgetItem(str(item["quantity"]))
            if item["quantity"] <= item["low_stock_threshold"]:
                qty_item.setForeground(Qt.GlobalColor.red)
            self.products_table.setItem(row, 4, qty_item)

            btn_add = QPushButton("+ أضف")
            btn_add.setObjectName("btn_success")
            btn_add.clicked.connect(lambda _, iid=item["id"]: self._add_to_cart(iid))
            self.products_table.setCellWidget(row, 5, btn_add)

    def _on_search(self, text):
        if text.strip():
            items = db.search_inventory(text.strip())
        else:
            items = db.get_all_inventory()
        self._populate_products(items)

    def _add_to_cart(self, item_id):
        item = db.get_inventory_item(item_id)
        if not item or item["quantity"] <= 0:
            QMessageBox.warning(self, "تنبيه", "المنتج غير متاح")
            return

        # Check if already in cart
        for cart_item in self.cart:
            if cart_item["item"]["id"] == item_id:
                max_qty = item["quantity"]
                if cart_item["quantity"] >= max_qty:
                    QMessageBox.warning(self, "تنبيه", "تم الوصول للحد الأقصى من المخزون")
                    return
                cart_item["quantity"] += 1
                self._refresh_cart()
                return

        # Ask for quantity and price
        dlg = QDialog(self)
        dlg.setWindowTitle(f"إضافة: {item['name']}")
        dlg.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        dlg.setMinimumWidth(350)
        form = QFormLayout(dlg)

        lbl = QLabel(f"المتاح: {item['quantity']}")
        lbl.setObjectName("subtitle")
        form.addRow(lbl)

        qty_spin = QSpinBox()
        qty_spin.setMinimum(1)
        qty_spin.setMaximum(item["quantity"])
        qty_spin.setValue(1)
        form.addRow("الكمية:", qty_spin)

        price_spin = QDoubleSpinBox()
        price_spin.setMaximum(999999)
        price_spin.setDecimals(2)
        price_spin.setValue(item["sell_price"])
        form.addRow("سعر البيع:", price_spin)

        btns = QHBoxLayout()
        btn_ok = QPushButton("إضافة للسلة")
        btn_ok.setObjectName("btn_success")
        btn_ok.clicked.connect(dlg.accept)
        btn_cancel = QPushButton("إلغاء")
        btn_cancel.setObjectName("btn_secondary")
        btn_cancel.clicked.connect(dlg.reject)
        btns.addWidget(btn_ok)
        btns.addWidget(btn_cancel)
        form.addRow(btns)

        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.cart.append({
                "item": dict(item),
                "quantity": qty_spin.value(),
                "sell_price": price_spin.value(),
            })
            self._refresh_cart()

    def _refresh_cart(self):
        self.cart_table.setRowCount(len(self.cart))
        total = 0
        profit = 0
        for row, entry in enumerate(self.cart):
            item = entry["item"]
            qty = entry["quantity"]
            price = entry["sell_price"]
            line_total = qty * price
            line_profit = qty * (price - item["buy_price"])
            total += line_total
            profit += line_profit

            self.cart_table.setItem(row, 0, QTableWidgetItem(item["id"]))
            self.cart_table.setItem(row, 1, QTableWidgetItem(item["name"]))
            self.cart_table.setItem(row, 2, QTableWidgetItem(str(qty)))
            self.cart_table.setItem(row, 3, QTableWidgetItem(format_currency(price)))
            self.cart_table.setItem(row, 4, QTableWidgetItem(format_currency(line_total)))

            btn_remove = QPushButton("X")
            btn_remove.setObjectName("btn_danger")
            btn_remove.clicked.connect(lambda _, r=row: self._remove_from_cart(r))
            self.cart_table.setCellWidget(row, 5, btn_remove)

        self.total_label.setText(f"الإجمالي: {format_currency(total)}")
        self.profit_label.setText(f"الربح: {format_currency(profit)}")

    def _remove_from_cart(self, row):
        if 0 <= row < len(self.cart):
            self.cart.pop(row)
            self._refresh_cart()

    def _clear_cart(self):
        if self.cart:
            reply = QMessageBox.question(
                self, "تأكيد", "هل تريد مسح السلة بالكامل؟",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.cart.clear()
                self._refresh_cart()

    def _checkout(self):
        if not self.cart:
            QMessageBox.warning(self, "تنبيه", "السلة فارغة")
            return

        vault_id = self.vault_combo.currentData()
        if not vault_id:
            QMessageBox.warning(self, "تنبيه", "يرجى اختيار الخزنة")
            return

        # Calculate totals for confirmation
        total = sum(e["quantity"] * e["sell_price"] for e in self.cart)
        items_count = sum(e["quantity"] for e in self.cart)

        reply = QMessageBox.question(
            self, "تأكيد البيع",
            f"عدد المنتجات: {items_count}\n"
            f"الإجمالي: {format_currency(total)}\n\n"
            "هل تريد تأكيد البيع؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        # Process each cart item
        all_receipts = []
        total_profit = 0
        for entry in self.cart:
            item = entry["item"]
            try:
                sale_id, profit = db.record_sale(
                    item["id"], entry["quantity"], entry["sell_price"],
                    item["buy_price"], vault_id,
                )
                total_profit += profit
                receipt = generate_sale_receipt(
                    item["name"], entry["quantity"], entry["sell_price"],
                    entry["quantity"] * entry["sell_price"], sale_id,
                )
                all_receipts.append(receipt)
            except ValueError as e:
                QMessageBox.warning(self, "خطأ", f"فشل بيع {item['name']}: {e}")

        self.cart.clear()
        self._refresh_cart()
        self._refresh_products()
        self._refresh_history()

        # Offer to save receipt
        if all_receipts:
            combined = "\n\n".join(all_receipts)
            reply = QMessageBox.question(
                self, "تم البيع بنجاح",
                f"تم البيع بنجاح!\n"
                f"إجمالي الربح: {format_currency(total_profit)}\n\n"
                "هل تريد حفظ الإيصال؟",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                from datetime import datetime
                fname = f"sale_batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                path = save_receipt_to_file(combined, fname)
                QMessageBox.information(self, "تم", f"تم حفظ الإيصال:\n{path}")

    def _refresh_history(self):
        from_date = self.date_from.date().toString("yyyy-MM-dd")
        to_date = self.date_to.date().toString("yyyy-MM-dd")
        sales = db.get_sales(from_date, to_date)

        self.history_table.setRowCount(len(sales))
        total_sales = 0
        total_profit = 0
        for row, sale in enumerate(sales):
            self.history_table.setItem(row, 0, QTableWidgetItem(sale["item_name"]))
            self.history_table.setItem(row, 1, QTableWidgetItem(str(sale["quantity"])))
            self.history_table.setItem(row, 2, QTableWidgetItem(format_currency(sale["unit_sell_price"])))
            self.history_table.setItem(row, 3, QTableWidgetItem(format_currency(sale["total"])))
            self.history_table.setItem(row, 4, QTableWidgetItem(format_currency(sale["profit"])))
            self.history_table.setItem(row, 5, QTableWidgetItem(sale["created_at"] or ""))
            total_sales += sale["total"]
            total_profit += sale["profit"]

        # Update summary
        while self.summary_layout.count():
            child = self.summary_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        sales_lbl = QLabel(f"إجمالي المبيعات: {format_currency(total_sales)}")
        sales_lbl.setStyleSheet("font-size: 14px; font-weight: bold;")
        self.summary_layout.addWidget(sales_lbl)

        if self.user_role == "admin":
            profit_lbl = QLabel(f"إجمالي الأرباح: {format_currency(total_profit)}")
            profit_lbl.setStyleSheet("font-size: 14px; font-weight: bold; color: #1a7a1a;")
            self.summary_layout.addWidget(profit_lbl)

        self.summary_layout.addStretch()

    def refresh_table(self):
        """Called by main window on navigation."""
        self._refresh_products()
        self._refresh_history()
        # Refresh vault combo
        self.vault_combo.clear()
        vaults = db.get_all_vaults()
        for v in vaults:
            self.vault_combo.addItem(v["name"], v["id"])
