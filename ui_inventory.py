"""
Maestro ERP - Inventory Module UI
Item management, selling to students, stock tracking.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QTableWidget, QTableWidgetItem, QComboBox, QMessageBox, QDialog,
    QFormLayout, QDoubleSpinBox, QSpinBox, QHeaderView, QAbstractItemView,
    QGroupBox
)
from PyQt6.QtCore import Qt

import database_manager as db


class InventoryWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        title = QLabel("المخزون والمبيعات")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #2980b9; margin-bottom: 10px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Add item form
        form_box = QGroupBox("اضافة عنصر جديد")
        form_layout = QHBoxLayout(form_box)

        self.inp_name = QLineEdit()
        self.inp_name.setPlaceholderText("اسم العنصر")
        self.inp_stock = QSpinBox()
        self.inp_stock.setMaximum(99999)
        self.inp_price = QDoubleSpinBox()
        self.inp_price.setMaximum(99999)
        self.inp_price.setSuffix(" جنيه")

        btn_add = QPushButton("اضافة")
        btn_add.setStyleSheet("background-color: #27ae60; color: #ffffff;")
        btn_add.clicked.connect(self.add_item)

        form_layout.addWidget(QLabel("الاسم:"))
        form_layout.addWidget(self.inp_name)
        form_layout.addWidget(QLabel("الكمية:"))
        form_layout.addWidget(self.inp_stock)
        form_layout.addWidget(QLabel("السعر:"))
        form_layout.addWidget(self.inp_price)
        form_layout.addWidget(btn_add)
        layout.addWidget(form_box)

        # Items table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["#", "الاسم", "الكمية", "السعر", "بيع", "اجراءات"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        layout.addWidget(self.table)

    def refresh(self):
        items = db.get_all_inventory()
        self.table.setRowCount(len(items))
        for i, item in enumerate(items):
            self.table.setItem(i, 0, QTableWidgetItem(str(item['id'])))
            self.table.setItem(i, 1, QTableWidgetItem(item['item_name']))
            self.table.setItem(i, 2, QTableWidgetItem(str(item['stock'])))
            self.table.setItem(i, 3, QTableWidgetItem(f"{item['price']:.2f}"))

            # Sell button
            btn_sell = QPushButton("بيع")
            btn_sell.setStyleSheet("background-color: #2980b9; color: #ffffff;")
            btn_sell.clicked.connect(lambda _, iid=item['id']: self.sell_dialog(iid))
            self.table.setCellWidget(i, 4, btn_sell)

            # Edit/Delete
            w = QWidget()
            bl = QHBoxLayout(w)
            bl.setContentsMargins(2, 2, 2, 2)
            btn_edit = QPushButton("تعديل")
            btn_edit.clicked.connect(lambda _, iid=item['id']: self.edit_item(iid))
            btn_del = QPushButton("حذف")
            btn_del.setStyleSheet("background-color: #c0392b; color: #ffffff;")
            btn_del.clicked.connect(lambda _, iid=item['id']: self.del_item(iid))
            bl.addWidget(btn_edit)
            bl.addWidget(btn_del)
            self.table.setCellWidget(i, 5, w)

    def add_item(self):
        name = self.inp_name.text().strip()
        if not name:
            return
        db.add_inventory_item(name, self.inp_stock.value(), self.inp_price.value())
        self.inp_name.clear()
        self.inp_stock.setValue(0)
        self.inp_price.setValue(0)
        self.refresh()

    def edit_item(self, item_id):
        items = db.get_all_inventory()
        item = next((x for x in items if x['id'] == item_id), None)
        if not item:
            return

        dlg = QDialog(self)
        dlg.setWindowTitle("تعديل العنصر")
        dlg.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        form = QFormLayout(dlg)

        inp_n = QLineEdit(item['item_name'])
        inp_s = QSpinBox()
        inp_s.setMaximum(99999)
        inp_s.setValue(item['stock'])
        inp_p = QDoubleSpinBox()
        inp_p.setMaximum(99999)
        inp_p.setValue(item['price'])

        form.addRow("الاسم:", inp_n)
        form.addRow("الكمية:", inp_s)
        form.addRow("السعر:", inp_p)

        btn = QPushButton("حفظ")
        btn.clicked.connect(lambda: self._save_item(dlg, item_id, inp_n.text(), inp_s.value(), inp_p.value()))
        form.addRow(btn)
        dlg.exec()

    def _save_item(self, dlg, iid, name, stock, price):
        if name.strip():
            db.update_inventory_item(iid, name.strip(), stock, price)
            dlg.accept()
            self.refresh()

    def del_item(self, item_id):
        reply = QMessageBox.question(self, "تأكيد", "هل انت متأكد من حذف هذا العنصر؟",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            db.delete_inventory_item(item_id)
            self.refresh()

    def sell_dialog(self, item_id):
        items = db.get_all_inventory()
        item = next((x for x in items if x['id'] == item_id), None)
        if not item:
            return

        dlg = QDialog(self)
        dlg.setWindowTitle(f"بيع - {item['item_name']}")
        dlg.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        dlg.setMinimumWidth(400)
        form = QFormLayout(dlg)

        form.addRow("المتاح:", QLabel(str(item['stock'])))
        form.addRow("السعر:", QLabel(f"{item['price']:.2f} جنيه"))

        inp_qty = QSpinBox()
        inp_qty.setRange(1, item['stock'] if item['stock'] > 0 else 1)
        form.addRow("الكمية:", inp_qty)

        combo_student = QComboBox()
        combo_student.addItem("-- بدون طالب --", None)
        for s in db.get_all_students():
            combo_student.addItem(s['name'], s['id'])
        form.addRow("الطالب (اختياري):", combo_student)

        btn = QPushButton("تأكيد البيع")
        btn.setStyleSheet("background-color: #27ae60; color: #ffffff;")
        btn.clicked.connect(lambda: self._do_sell(dlg, item_id, inp_qty.value(), combo_student.currentData()))
        form.addRow(btn)
        dlg.exec()

    def _do_sell(self, dlg, item_id, qty, student_id):
        success, msg = db.sell_inventory_item(item_id, qty, student_id)
        if success:
            QMessageBox.information(self, "تم", msg)
            dlg.accept()
            self.refresh()
        else:
            QMessageBox.warning(self, "خطأ", msg)
