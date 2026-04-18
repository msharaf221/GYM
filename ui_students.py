"""
Maestro ERP - Students Dashboard Module
The Command Center: student management, attendance, calendar, ledger, payments.
"""

import json
import calendar as cal_mod
from datetime import datetime, date

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QTableWidget, QTableWidgetItem, QComboBox, QMessageBox, QDialog,
    QFormLayout, QCheckBox, QHeaderView, QAbstractItemView, QGroupBox,
    QDoubleSpinBox, QDateEdit, QGridLayout, QScrollArea, QSpinBox,
    QTabWidget
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor

import database_manager as db
from invoice_engine import generate_invoice, open_pdf

DAYS_AR_MAP = {
    "Saturday": "السبت", "Sunday": "الاحد", "Monday": "الاثنين",
    "Tuesday": "الثلاثاء", "Wednesday": "الاربعاء", "Thursday": "الخميس",
    "Friday": "الجمعة"
}


class StudentsWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        # Title & total debts
        header = QHBoxLayout()
        title = QLabel("لوحة الطلاب")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #00bcd4;")
        self.lbl_debts = QLabel("اجمالي ديون المركز: 0 جنيه")
        self.lbl_debts.setStyleSheet("font-size: 16px; color: #e74c3c; font-weight: bold;")
        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.lbl_debts)
        layout.addLayout(header)

        # Tabs: Students List & Attendance
        self.tabs = QTabWidget()
        self.tab_list = QWidget()
        self.tab_attendance = QWidget()
        self.tabs.addTab(self.tab_list, "قائمة الطلاب")
        self.tabs.addTab(self.tab_attendance, "الحضور والغياب")
        layout.addWidget(self.tabs)

        self._build_students_tab()
        self._build_attendance_tab()

    def _build_students_tab(self):
        layout = QVBoxLayout(self.tab_list)

        # Search & actions
        toolbar = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("بحث بالاسم او الهاتف...")
        self.search_input.textChanged.connect(self.search_students)

        btn_add = QPushButton("اضافة طالب")
        btn_add.setStyleSheet("background-color: #27ae60;")
        btn_add.clicked.connect(self.add_student_dialog)

        btn_transfer = QPushButton("نقل المحددين")
        btn_transfer.clicked.connect(self.transfer_selected)

        btn_delete_sel = QPushButton("حذف المحددين")
        btn_delete_sel.setStyleSheet("background-color: #c0392b;")
        btn_delete_sel.clicked.connect(self.delete_selected)

        btn_bulk_pay = QPushButton("دفع جماعي")
        btn_bulk_pay.setStyleSheet("background-color: #2980b9;")
        btn_bulk_pay.clicked.connect(self.bulk_pay_selected)

        toolbar.addWidget(self.search_input)
        toolbar.addWidget(btn_add)
        toolbar.addWidget(btn_transfer)
        toolbar.addWidget(btn_delete_sel)
        toolbar.addWidget(btn_bulk_pay)
        layout.addLayout(toolbar)

        # Students table with checkboxes
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "تحديد", "#", "الاسم", "المجموعة", "المديونية", "اخر حضور", "الحالة", "اجراءات"
        ])
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        layout.addWidget(self.table)

    def _build_attendance_tab(self):
        layout = QVBoxLayout(self.tab_attendance)

        info = QLabel("الحضور الذكي: يعرض فقط طلاب المجموعات المجدولة لهذا اليوم")
        info.setStyleSheet("color: #f39c12; font-size: 13px; margin-bottom: 8px;")
        layout.addWidget(info)

        ctrl = QHBoxLayout()
        self.combo_att_group = QComboBox()
        self.combo_att_group.currentIndexChanged.connect(self.load_attendance_students)
        btn_save_att = QPushButton("حفظ الحضور")
        btn_save_att.setStyleSheet("background-color: #27ae60;")
        btn_save_att.clicked.connect(self.save_attendance)
        ctrl.addWidget(QLabel("المجموعة:"))
        ctrl.addWidget(self.combo_att_group)
        ctrl.addStretch()
        ctrl.addWidget(btn_save_att)
        layout.addLayout(ctrl)

        self.att_table = QTableWidget()
        self.att_table.setColumnCount(4)
        self.att_table.setHorizontalHeaderLabels(["#", "الاسم", "الحالة", "student_id"])
        self.att_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.att_table.setColumnHidden(3, True)
        layout.addWidget(self.att_table)

    def refresh(self):
        self._load_debts()
        self._load_students(db.get_all_students())
        self._load_today_groups()

    def _load_debts(self):
        total = db.get_total_center_debts()
        self.lbl_debts.setText(f"اجمالي ديون المركز: {total:.2f} جنيه")

    def _load_students(self, students):
        self.table.setRowCount(len(students))
        for i, s in enumerate(students):
            # Checkbox
            cb = QCheckBox()
            cb.setProperty("student_id", s['id'])
            cb_widget = QWidget()
            cb_layout = QHBoxLayout(cb_widget)
            cb_layout.addWidget(cb)
            cb_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cb_layout.setContentsMargins(0, 0, 0, 0)
            self.table.setCellWidget(i, 0, cb_widget)

            self.table.setItem(i, 1, QTableWidgetItem(str(s['id'])))
            self.table.setItem(i, 2, QTableWidgetItem(s['name']))
            self.table.setItem(i, 3, QTableWidgetItem(s['group_name'] or "-"))

            debt = s['debt'] if s['debt'] else 0
            debt_item = QTableWidgetItem(f"{debt:.2f}")
            if debt > 0:
                debt_item.setForeground(QColor("#e74c3c"))
            self.table.setItem(i, 4, debt_item)

            self.table.setItem(i, 5, QTableWidgetItem(s['last_attendance'] or "-"))
            self.table.setItem(i, 6, QTableWidgetItem("نشط" if s['status'] == 'active' else "متوقف"))

            # Actions
            w = QWidget()
            bl = QHBoxLayout(w)
            bl.setContentsMargins(2, 2, 2, 2)

            btn_pay = QPushButton("دفع")
            btn_pay.setStyleSheet("background-color: #27ae60;")
            btn_pay.clicked.connect(lambda _, sid=s['id']: self.pay_dialog(sid))

            btn_profile = QPushButton("ملف")
            btn_profile.clicked.connect(lambda _, sid=s['id']: self.student_profile(sid))

            btn_edit = QPushButton("تعديل")
            btn_edit.clicked.connect(lambda _, sid=s['id']: self.edit_student(sid))

            btn_del = QPushButton("حذف")
            btn_del.setStyleSheet("background-color: #c0392b;")
            btn_del.clicked.connect(lambda _, sid=s['id']: self.del_student(sid))

            bl.addWidget(btn_pay)
            bl.addWidget(btn_profile)
            bl.addWidget(btn_edit)
            bl.addWidget(btn_del)
            self.table.setCellWidget(i, 7, w)

            # Color row if debt > 0
            if debt > 0:
                for col in range(self.table.columnCount()):
                    item = self.table.item(i, col)
                    if item:
                        item.setBackground(QColor(50, 20, 20))

    def search_students(self, text):
        if text.strip():
            students = db.search_students(text.strip())
        else:
            students = db.get_all_students()
        self._load_students(students)

    def _get_selected_student_ids(self):
        ids = []
        for row in range(self.table.rowCount()):
            w = self.table.cellWidget(row, 0)
            if w:
                cb = w.findChild(QCheckBox)
                if cb and cb.isChecked():
                    ids.append(cb.property("student_id"))
        return ids

    # ---- ADD STUDENT ----
    def add_student_dialog(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("اضافة طالب جديد")
        dlg.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        dlg.setMinimumWidth(400)
        form = QFormLayout(dlg)

        inp_name = QLineEdit()
        inp_phone = QLineEdit()
        combo_group = QComboBox()
        combo_group.addItem("-- اختر المجموعة --", None)
        for g in db.get_all_groups():
            combo_group.addItem(f"{g['name']} ({g['course_name'] or ''})", g['id'])

        inp_total = QDoubleSpinBox()
        inp_total.setMaximum(99999)
        inp_total.setSuffix(" جنيه")

        inp_paid = QDoubleSpinBox()
        inp_paid.setMaximum(99999)
        inp_paid.setSuffix(" جنيه")

        inp_due = QDateEdit()
        inp_due.setDate(QDate.currentDate().addMonths(1))
        inp_due.setCalendarPopup(True)

        form.addRow("الاسم:", inp_name)
        form.addRow("الهاتف:", inp_phone)
        form.addRow("المجموعة:", combo_group)
        form.addRow("المبلغ المطلوب:", inp_total)
        form.addRow("المبلغ المدفوع:", inp_paid)
        form.addRow("تاريخ الاستحقاق:", inp_due)

        btn = QPushButton("اضافة")
        btn.clicked.connect(lambda: self._save_new_student(
            dlg, inp_name.text(), inp_phone.text(), combo_group.currentData(),
            inp_total.value(), inp_paid.value(), inp_due.date().toString("yyyy-MM-dd")))
        form.addRow(btn)
        dlg.exec()

    def _save_new_student(self, dlg, name, phone, group_id, total, paid, due_date):
        if not name.strip():
            QMessageBox.warning(self, "خطأ", "ادخل اسم الطالب")
            return
        student_id = db.add_student(name.strip(), phone.strip(), group_id)
        if group_id and total > 0:
            db.add_subscription(student_id, group_id, total, paid, due_date)
            if paid > 0:
                db.add_ledger_entry(student_id, "دفعة اولية عند التسجيل", 0, paid)
                db.add_finance('income', 'اشتراكات', paid, f"دفعة من {name.strip()}", student_id)
            if total > paid:
                db.add_ledger_entry(student_id, "اشتراك جديد", total - paid, 0)
        dlg.accept()
        self.refresh()

    # ---- EDIT STUDENT ----
    def edit_student(self, student_id):
        student = db.get_student_by_id(student_id)
        if not student:
            return
        dlg = QDialog(self)
        dlg.setWindowTitle("تعديل بيانات الطالب")
        dlg.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        dlg.setMinimumWidth(400)
        form = QFormLayout(dlg)

        inp_name = QLineEdit(student['name'])
        inp_phone = QLineEdit(student['phone'] or "")
        combo_group = QComboBox()
        combo_group.addItem("-- بدون مجموعة --", None)
        for g in db.get_all_groups():
            combo_group.addItem(f"{g['name']} ({g['course_name'] or ''})", g['id'])
            if g['id'] == student['group_id']:
                combo_group.setCurrentIndex(combo_group.count() - 1)

        combo_status = QComboBox()
        combo_status.addItem("نشط", "active")
        combo_status.addItem("متوقف", "inactive")
        if student['status'] != 'active':
            combo_status.setCurrentIndex(1)

        form.addRow("الاسم:", inp_name)
        form.addRow("الهاتف:", inp_phone)
        form.addRow("المجموعة:", combo_group)
        form.addRow("الحالة:", combo_status)

        btn = QPushButton("حفظ")
        btn.clicked.connect(lambda: self._update_student(
            dlg, student_id, inp_name.text(), inp_phone.text(),
            combo_group.currentData(), combo_status.currentData()))
        form.addRow(btn)
        dlg.exec()

    def _update_student(self, dlg, sid, name, phone, gid, status):
        if not name.strip():
            return
        db.update_student(sid, name.strip(), phone.strip(), gid, status)
        dlg.accept()
        self.refresh()

    # ---- DELETE ----
    def del_student(self, student_id):
        reply = QMessageBox.question(self, "تأكيد", "هل انت متأكد من حذف هذا الطالب؟",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            db.delete_student(student_id)
            self.refresh()

    # ---- BATCH ACTIONS ----
    def transfer_selected(self):
        ids = self._get_selected_student_ids()
        if not ids:
            QMessageBox.information(self, "تنبيه", "حدد طلاب اولا")
            return
        dlg = QDialog(self)
        dlg.setWindowTitle("نقل الطلاب")
        dlg.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        form = QFormLayout(dlg)
        combo = QComboBox()
        for g in db.get_all_groups():
            combo.addItem(f"{g['name']} ({g['course_name'] or ''})", g['id'])
        form.addRow("المجموعة الجديدة:", combo)
        btn = QPushButton("نقل")
        btn.clicked.connect(lambda: self._do_transfer(dlg, ids, combo.currentData()))
        form.addRow(btn)
        dlg.exec()

    def _do_transfer(self, dlg, ids, new_gid):
        if new_gid is None:
            return
        db.transfer_students_to_group(ids, new_gid)
        dlg.accept()
        self.refresh()

    def delete_selected(self):
        ids = self._get_selected_student_ids()
        if not ids:
            QMessageBox.information(self, "تنبيه", "حدد طلاب اولا")
            return
        reply = QMessageBox.question(self, "تأكيد", f"هل انت متأكد من حذف {len(ids)} طالب؟",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            db.delete_students_bulk(ids)
            self.refresh()

    def bulk_pay_selected(self):
        ids = self._get_selected_student_ids()
        if not ids:
            QMessageBox.information(self, "تنبيه", "حدد طلاب اولا")
            return
        dlg = QDialog(self)
        dlg.setWindowTitle("دفع جماعي")
        dlg.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        form = QFormLayout(dlg)
        inp_amount = QDoubleSpinBox()
        inp_amount.setMaximum(99999)
        inp_amount.setSuffix(" جنيه")
        form.addRow("المبلغ لكل طالب:", inp_amount)
        btn = QPushButton("تنفيذ الدفع")
        btn.clicked.connect(lambda: self._do_bulk_pay(dlg, ids, inp_amount.value()))
        form.addRow(btn)
        dlg.exec()

    def _do_bulk_pay(self, dlg, ids, amount):
        if amount <= 0:
            return
        for sid in ids:
            self._process_payment(sid, amount)
        dlg.accept()
        self.refresh()

    # ---- PAYMENT ----
    def pay_dialog(self, student_id):
        student = db.get_student_by_id(student_id)
        sub = db.get_latest_subscription(student_id)
        if not student:
            return

        dlg = QDialog(self)
        dlg.setWindowTitle(f"دفع - {student['name']}")
        dlg.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        dlg.setMinimumWidth(400)
        form = QFormLayout(dlg)

        debt = 0
        if sub:
            debt = sub['total_required'] - sub['paid_amount']

        form.addRow("المديونية الحالية:", QLabel(f"{debt:.2f} جنيه"))

        inp_amount = QDoubleSpinBox()
        inp_amount.setMaximum(99999)
        inp_amount.setValue(debt if debt > 0 else 0)
        inp_amount.setSuffix(" جنيه")
        form.addRow("المبلغ المدفوع:", inp_amount)

        btn = QPushButton("تأكيد الدفع وطباعة الايصال")
        btn.setStyleSheet("background-color: #27ae60;")
        btn.clicked.connect(lambda: self._confirm_payment(dlg, student_id, inp_amount.value()))
        form.addRow(btn)
        dlg.exec()

    def _confirm_payment(self, dlg, student_id, amount):
        if amount <= 0:
            return
        self._process_payment(student_id, amount, print_invoice=True)
        dlg.accept()
        self.refresh()

    def _process_payment(self, student_id, amount, print_invoice=False):
        student = db.get_student_by_id(student_id)
        sub = db.get_latest_subscription(student_id)

        if sub:
            new_paid = sub['paid_amount'] + amount
            db.update_subscription_paid(sub['id'], new_paid)
            remaining = sub['total_required'] - new_paid
        else:
            remaining = 0

        db.add_ledger_entry(student_id, f"دفعة مالية", 0, amount)
        db.add_finance('income', 'اشتراكات', amount,
                       f"دفعة من {student['name']}", student_id)

        if print_invoice:
            group_name = student['group_name'] or "-"
            filepath = generate_invoice(
                student_name=student['name'],
                group_name=group_name,
                amount_paid=amount,
                remaining_debt=max(remaining, 0)
            )
            if filepath:
                open_pdf(filepath)
                QMessageBox.information(self, "تم", f"تم حفظ الايصال: {filepath}")
            else:
                QMessageBox.information(self, "تم", "تم تسجيل الدفعة (مكتبة PDF غير متوفرة)")

    # ---- STUDENT PROFILE ----
    def student_profile(self, student_id):
        student = db.get_student_by_id(student_id)
        if not student:
            return

        dlg = QDialog(self)
        dlg.setWindowTitle(f"ملف الطالب - {student['name']}")
        dlg.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        dlg.setMinimumSize(700, 500)
        layout = QVBoxLayout(dlg)

        # Info header
        info = QLabel(f"الاسم: {student['name']}  |  الهاتف: {student['phone'] or '-'}  |  المجموعة: {student['group_name'] or '-'}")
        info.setStyleSheet("font-size: 14px; font-weight: bold; color: #00bcd4; padding: 8px;")
        layout.addWidget(info)

        tabs = QTabWidget()

        # Ledger tab
        ledger_tab = QWidget()
        ledger_layout = QVBoxLayout(ledger_tab)
        ledger_table = QTableWidget()
        ledger_entries = db.get_student_ledger(student_id)
        ledger_table.setColumnCount(5)
        ledger_table.setHorizontalHeaderLabels(["التاريخ", "الوصف", "مدين", "دائن", "الرصيد"])
        ledger_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        ledger_table.setRowCount(len(ledger_entries))
        for i, e in enumerate(ledger_entries):
            ledger_table.setItem(i, 0, QTableWidgetItem(e['date']))
            ledger_table.setItem(i, 1, QTableWidgetItem(e['description'] or ""))
            ledger_table.setItem(i, 2, QTableWidgetItem(f"{e['debit']:.2f}"))
            ledger_table.setItem(i, 3, QTableWidgetItem(f"{e['credit']:.2f}"))
            ledger_table.setItem(i, 4, QTableWidgetItem(f"{e['balance']:.2f}"))
        ledger_layout.addWidget(ledger_table)
        tabs.addTab(ledger_tab, "كشف الحساب")

        # Calendar tab
        cal_tab = QWidget()
        cal_layout = QVBoxLayout(cal_tab)

        cal_ctrl = QHBoxLayout()
        self._cal_month = QSpinBox()
        self._cal_month.setRange(1, 12)
        self._cal_month.setValue(date.today().month)
        self._cal_year = QSpinBox()
        self._cal_year.setRange(2020, 2040)
        self._cal_year.setValue(date.today().year)
        btn_load_cal = QPushButton("عرض")
        cal_ctrl.addWidget(QLabel("الشهر:"))
        cal_ctrl.addWidget(self._cal_month)
        cal_ctrl.addWidget(QLabel("السنة:"))
        cal_ctrl.addWidget(self._cal_year)
        cal_ctrl.addWidget(btn_load_cal)
        cal_ctrl.addStretch()
        cal_layout.addLayout(cal_ctrl)

        cal_grid = QGridLayout()
        # Day headers
        day_names = ["سبت", "احد", "اثنين", "ثلاثاء", "اربعاء", "خميس", "جمعة"]
        for col, d in enumerate(day_names):
            lbl = QLabel(d)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("font-weight: bold; color: #00bcd4;")
            cal_grid.addWidget(lbl, 0, col)

        cal_container = QWidget()
        cal_container.setLayout(cal_grid)
        cal_layout.addWidget(cal_container)

        def load_calendar():
            # Clear old cells
            for row in range(1, 7):
                for col in range(7):
                    item = cal_grid.itemAtPosition(row, col)
                    if item and item.widget():
                        item.widget().deleteLater()

            month = self._cal_month.value()
            year = self._cal_year.value()
            att_records = db.get_student_attendance_for_month(student_id, year, month)
            att_map = {}
            for a in att_records:
                day_num = int(a['date'].split('-')[2])
                att_map[day_num] = a['status']

            first_day, num_days = cal_mod.monthrange(year, month)
            # Adjust: Python Monday=0, we want Saturday=0
            first_day = (first_day + 2) % 7

            row = 1
            col = first_day
            for day in range(1, num_days + 1):
                lbl = QLabel(str(day))
                lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                lbl.setFixedSize(40, 40)

                status = att_map.get(day)
                if status == 'present':
                    lbl.setStyleSheet("background-color: #27ae60; color: white; border-radius: 5px; font-weight: bold;")
                elif status == 'absent':
                    lbl.setStyleSheet("background-color: #e74c3c; color: white; border-radius: 5px; font-weight: bold;")
                elif status == 'charged_absence':
                    lbl.setStyleSheet("background-color: #f39c12; color: white; border-radius: 5px; font-weight: bold;")
                else:
                    lbl.setStyleSheet("background-color: #2c2c3e; color: #aaa; border-radius: 5px;")

                cal_grid.addWidget(lbl, row, col)
                col += 1
                if col > 6:
                    col = 0
                    row += 1

        btn_load_cal.clicked.connect(load_calendar)
        load_calendar()

        # Legend
        legend = QHBoxLayout()
        for color, text in [("#27ae60", "حاضر"), ("#e74c3c", "غائب"), ("#f39c12", "غياب محسوب")]:
            box = QLabel(f"  {text}  ")
            box.setStyleSheet(f"background-color: {color}; color: white; border-radius: 3px; padding: 2px 6px;")
            legend.addWidget(box)
        legend.addStretch()
        cal_layout.addLayout(legend)

        tabs.addTab(cal_tab, "تقويم الحضور")

        # Subscriptions tab
        sub_tab = QWidget()
        sub_layout = QVBoxLayout(sub_tab)
        sub_table = QTableWidget()
        subs = db.get_student_subscriptions(student_id)
        sub_table.setColumnCount(5)
        sub_table.setHorizontalHeaderLabels(["المجموعة", "المطلوب", "المدفوع", "المتبقي", "الاستحقاق"])
        sub_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        sub_table.setRowCount(len(subs))
        for i, s in enumerate(subs):
            sub_table.setItem(i, 0, QTableWidgetItem(s['group_name'] or "-"))
            sub_table.setItem(i, 1, QTableWidgetItem(f"{s['total_required']:.2f}"))
            sub_table.setItem(i, 2, QTableWidgetItem(f"{s['paid_amount']:.2f}"))
            remaining = s['total_required'] - s['paid_amount']
            sub_table.setItem(i, 3, QTableWidgetItem(f"{remaining:.2f}"))
            sub_table.setItem(i, 4, QTableWidgetItem(s['due_date'] or "-"))
        sub_layout.addWidget(sub_table)
        tabs.addTab(sub_tab, "الاشتراكات")

        layout.addWidget(tabs)
        dlg.exec()

    # ---- ATTENDANCE ----
    def _load_today_groups(self):
        today_en = date.today().strftime("%A")
        today_ar = DAYS_AR_MAP.get(today_en, "")
        self.combo_att_group.clear()
        self.combo_att_group.addItem("-- اختر المجموعة --", None)
        groups = db.get_groups_for_today(today_ar)
        for g in groups:
            self.combo_att_group.addItem(f"{g['name']} ({g['course_name'] or ''})", g['id'])

    def load_attendance_students(self):
        group_id = self.combo_att_group.currentData()
        if group_id is None:
            self.att_table.setRowCount(0)
            return

        students = db.get_students_by_group(group_id)
        today_str = date.today().isoformat()
        existing = db.get_attendance_for_date(group_id, today_str)
        att_map = {a['student_id']: a['status'] for a in existing}

        self.att_table.setRowCount(len(students))
        for i, s in enumerate(students):
            self.att_table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            self.att_table.setItem(i, 1, QTableWidgetItem(s['name']))
            self.att_table.setItem(i, 3, QTableWidgetItem(str(s['id'])))

            combo = QComboBox()
            combo.addItem("حاضر", "present")
            combo.addItem("غائب", "absent")
            combo.addItem("غياب محسوب", "charged_absence")

            current_status = att_map.get(s['id'], 'present')
            idx_map = {'present': 0, 'absent': 1, 'charged_absence': 2}
            combo.setCurrentIndex(idx_map.get(current_status, 0))

            self.att_table.setCellWidget(i, 2, combo)

    def save_attendance(self):
        group_id = self.combo_att_group.currentData()
        if group_id is None:
            return

        today_str = date.today().isoformat()
        for row in range(self.att_table.rowCount()):
            sid_item = self.att_table.item(row, 3)
            combo = self.att_table.cellWidget(row, 2)
            if sid_item and combo:
                student_id = int(sid_item.text())
                status = combo.currentData()
                db.mark_attendance(student_id, group_id, status, today_str)

        QMessageBox.information(self, "تم", "تم حفظ الحضور بنجاح")
