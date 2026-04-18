"""
Maestro ERP - Finance Module UI
Income/Expense tracking, summary dashboard.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QTableWidget, QTableWidgetItem, QComboBox, QMessageBox, QDialog,
    QFormLayout, QDoubleSpinBox, QHeaderView, QAbstractItemView, QGroupBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

import database_manager as db


class FinancesWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        title = QLabel("الخزينة المالية")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #2980b9; margin-bottom: 10px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Summary cards
        cards = QHBoxLayout()
        self.lbl_income = self._make_card("اجمالي الدخل", "0", "#27ae60")
        self.lbl_expense = self._make_card("اجمالي المصروفات", "0", "#e74c3c")
        self.lbl_net = self._make_card("صافي الرصيد", "0", "#2980b9")
        self.lbl_debts = self._make_card("اجمالي الديون", "0", "#f39c12")
        cards.addWidget(self.lbl_income)
        cards.addWidget(self.lbl_expense)
        cards.addWidget(self.lbl_net)
        cards.addWidget(self.lbl_debts)
        layout.addLayout(cards)

        # Add transaction
        form_box = QGroupBox("اضافة معاملة مالية")
        form_layout = QHBoxLayout(form_box)

        self.combo_type = QComboBox()
        self.combo_type.addItem("دخل", "income")
        self.combo_type.addItem("مصروف", "expense")

        self.inp_category = QLineEdit()
        self.inp_category.setPlaceholderText("التصنيف")

        self.inp_amount = QDoubleSpinBox()
        self.inp_amount.setMaximum(999999)
        self.inp_amount.setSuffix(" جنيه")

        self.inp_notes = QLineEdit()
        self.inp_notes.setPlaceholderText("ملاحظات")

        btn_add = QPushButton("اضافة")
        btn_add.setStyleSheet("background-color: #27ae60; color: #ffffff;")
        btn_add.clicked.connect(self.add_transaction)

        form_layout.addWidget(QLabel("النوع:"))
        form_layout.addWidget(self.combo_type)
        form_layout.addWidget(self.inp_category)
        form_layout.addWidget(self.inp_amount)
        form_layout.addWidget(self.inp_notes)
        form_layout.addWidget(btn_add)
        layout.addWidget(form_box)

        # Transactions table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "#", "النوع", "التصنيف", "المبلغ", "التاريخ", "ملاحظات", "حذف"
        ])
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        layout.addWidget(self.table)

    def _make_card(self, title, value, color):
        card = QGroupBox()
        card.setStyleSheet(f"""
            QGroupBox {{
                border: 2px solid {color};
                border-radius: 8px;
                padding: 10px;
                margin-top: 5px;
            }}
        """)
        lay = QVBoxLayout(card)
        lbl_title = QLabel(title)
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_title.setStyleSheet(f"color: {color}; font-size: 12px;")
        lbl_value = QLabel(value)
        lbl_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_value.setStyleSheet(f"color: {color}; font-size: 20px; font-weight: bold;")
        lbl_value.setObjectName("value_label")
        lay.addWidget(lbl_title)
        lay.addWidget(lbl_value)
        return card

    def _update_card(self, card, value):
        lbl = card.findChild(QLabel, "value_label")
        if lbl:
            lbl.setText(f"{value:.2f}")

    def refresh(self):
        summary = db.get_finance_summary()
        self._update_card(self.lbl_income, summary['income'])
        self._update_card(self.lbl_expense, summary['expense'])
        self._update_card(self.lbl_net, summary['net'])
        self._update_card(self.lbl_debts, db.get_total_center_debts())

        transactions = db.get_all_finance()
        self.table.setRowCount(len(transactions))
        for i, t in enumerate(transactions):
            self.table.setItem(i, 0, QTableWidgetItem(str(t['id'])))
            type_text = "دخل" if t['type'] == 'income' else "مصروف"
            type_item = QTableWidgetItem(type_text)
            if t['type'] == 'income':
                type_item.setForeground(QColor("#27ae60"))
            else:
                type_item.setForeground(QColor("#e74c3c"))
            self.table.setItem(i, 1, type_item)
            self.table.setItem(i, 2, QTableWidgetItem(t['category'] or "-"))
            self.table.setItem(i, 3, QTableWidgetItem(f"{t['amount']:.2f}"))
            self.table.setItem(i, 4, QTableWidgetItem(t['date'] or "-"))
            self.table.setItem(i, 5, QTableWidgetItem(t['notes'] or "-"))

            btn_del = QPushButton("حذف")
            btn_del.setStyleSheet("background-color: #c0392b; color: #ffffff;")
            btn_del.clicked.connect(lambda _, fid=t['id']: self.del_transaction(fid))
            self.table.setCellWidget(i, 6, btn_del)

    def add_transaction(self):
        tx_type = self.combo_type.currentData()
        category = self.inp_category.text().strip()
        amount = self.inp_amount.value()
        notes = self.inp_notes.text().strip()

        if amount <= 0:
            QMessageBox.warning(self, "خطأ", "ادخل مبلغ صحيح")
            return

        db.add_finance(tx_type, category or "عام", amount, notes)
        self.inp_category.clear()
        self.inp_amount.setValue(0)
        self.inp_notes.clear()
        self.refresh()

    def del_transaction(self, finance_id):
        reply = QMessageBox.question(self, "تأكيد", "هل انت متأكد من حذف هذه المعاملة؟",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            db.delete_finance(finance_id)
            self.refresh()
