"""
Maestro ERP - Settings Module UI
Manages Levels, Teachers, Courses, Course Schedules, and Groups.
Implements the Checkbox logic: Course days -> Group selects specific days.
"""

import json
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QLabel, QPushButton,
    QLineEdit, QTableWidget, QTableWidgetItem, QComboBox, QMessageBox,
    QDialog, QFormLayout, QCheckBox, QGroupBox, QDoubleSpinBox, QTimeEdit,
    QHeaderView, QAbstractItemView
)
from PyQt6.QtCore import Qt, QTime
import database_manager as db

DAYS_AR = ["السبت", "الاحد", "الاثنين", "الثلاثاء", "الاربعاء", "الخميس", "الجمعة"]


class SettingsWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        title = QLabel("الاعدادات والجداول")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #00bcd4; margin-bottom: 10px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        self.tabs = QTabWidget()
        self.tabs.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        self.tab_levels = LevelsTab()
        self.tab_teachers = TeachersTab()
        self.tab_courses = CoursesTab()
        self.tab_groups = GroupsTab()

        self.tabs.addTab(self.tab_levels, "المستويات")
        self.tabs.addTab(self.tab_teachers, "المعلمين")
        self.tabs.addTab(self.tab_courses, "الكورسات والجداول")
        self.tabs.addTab(self.tab_groups, "المجموعات")

        layout.addWidget(self.tabs)

        # Refresh groups tab when courses change
        self.tabs.currentChanged.connect(self._on_tab_changed)

    def _on_tab_changed(self, index):
        widget = self.tabs.widget(index)
        if hasattr(widget, 'refresh'):
            widget.refresh()

    def refresh_all(self):
        self.tab_levels.refresh()
        self.tab_teachers.refresh()
        self.tab_courses.refresh()
        self.tab_groups.refresh()


# ======================== LEVELS TAB ========================

class LevelsTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        # Add form
        form_layout = QHBoxLayout()
        self.input_name = QLineEdit()
        self.input_name.setPlaceholderText("اسم المستوى")
        btn_add = QPushButton("اضافة")
        btn_add.clicked.connect(self.add_level)
        form_layout.addWidget(self.input_name)
        form_layout.addWidget(btn_add)
        layout.addLayout(form_layout)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["#", "الاسم", "اجراءات"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        layout.addWidget(self.table)

        self.refresh()

    def refresh(self):
        levels = db.get_all_levels()
        self.table.setRowCount(len(levels))
        for i, lev in enumerate(levels):
            self.table.setItem(i, 0, QTableWidgetItem(str(lev['id'])))
            self.table.setItem(i, 1, QTableWidgetItem(lev['name']))

            btn_layout = QHBoxLayout()
            btn_edit = QPushButton("تعديل")
            btn_del = QPushButton("حذف")
            btn_del.setStyleSheet("background-color: #c0392b;")
            btn_edit.clicked.connect(lambda _, lid=lev['id'], n=lev['name']: self.edit_level(lid, n))
            btn_del.clicked.connect(lambda _, lid=lev['id']: self.del_level(lid))

            w = QWidget()
            bl = QHBoxLayout(w)
            bl.addWidget(btn_edit)
            bl.addWidget(btn_del)
            bl.setContentsMargins(2, 2, 2, 2)
            self.table.setCellWidget(i, 2, w)

    def add_level(self):
        name = self.input_name.text().strip()
        if not name:
            return
        if db.add_level(name):
            self.input_name.clear()
            self.refresh()
        else:
            QMessageBox.warning(self, "خطأ", "هذا المستوى موجود بالفعل")

    def edit_level(self, level_id, current_name):
        dlg = QDialog(self)
        dlg.setWindowTitle("تعديل المستوى")
        dlg.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        form = QFormLayout(dlg)
        inp = QLineEdit(current_name)
        form.addRow("الاسم:", inp)
        btn = QPushButton("حفظ")
        btn.clicked.connect(lambda: self._save_level(dlg, level_id, inp.text()))
        form.addRow(btn)
        dlg.exec()

    def _save_level(self, dlg, level_id, name):
        if name.strip():
            db.update_level(level_id, name.strip())
            dlg.accept()
            self.refresh()

    def del_level(self, level_id):
        reply = QMessageBox.question(self, "تأكيد", "هل انت متأكد من حذف هذا المستوى؟",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            db.delete_level(level_id)
            self.refresh()


# ======================== TEACHERS TAB ========================

class TeachersTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        form_layout = QHBoxLayout()
        self.inp_name = QLineEdit()
        self.inp_name.setPlaceholderText("اسم المعلم")
        self.inp_phone = QLineEdit()
        self.inp_phone.setPlaceholderText("الهاتف")
        self.inp_subject = QLineEdit()
        self.inp_subject.setPlaceholderText("المادة")
        btn_add = QPushButton("اضافة")
        btn_add.clicked.connect(self.add_teacher)
        form_layout.addWidget(self.inp_name)
        form_layout.addWidget(self.inp_phone)
        form_layout.addWidget(self.inp_subject)
        form_layout.addWidget(btn_add)
        layout.addLayout(form_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["#", "الاسم", "الهاتف", "المادة", "اجراءات"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        layout.addWidget(self.table)

        self.refresh()

    def refresh(self):
        teachers = db.get_all_teachers()
        self.table.setRowCount(len(teachers))
        for i, t in enumerate(teachers):
            self.table.setItem(i, 0, QTableWidgetItem(str(t['id'])))
            self.table.setItem(i, 1, QTableWidgetItem(t['name']))
            self.table.setItem(i, 2, QTableWidgetItem(t['phone'] or ""))
            self.table.setItem(i, 3, QTableWidgetItem(t['subject'] or ""))

            w = QWidget()
            bl = QHBoxLayout(w)
            btn_edit = QPushButton("تعديل")
            btn_del = QPushButton("حذف")
            btn_del.setStyleSheet("background-color: #c0392b;")
            btn_edit.clicked.connect(lambda _, tid=t['id']: self.edit_teacher(tid))
            btn_del.clicked.connect(lambda _, tid=t['id']: self.del_teacher(tid))
            bl.addWidget(btn_edit)
            bl.addWidget(btn_del)
            bl.setContentsMargins(2, 2, 2, 2)
            self.table.setCellWidget(i, 4, w)

    def add_teacher(self):
        name = self.inp_name.text().strip()
        if not name:
            return
        db.add_teacher(name, self.inp_phone.text().strip(), self.inp_subject.text().strip())
        self.inp_name.clear()
        self.inp_phone.clear()
        self.inp_subject.clear()
        self.refresh()

    def edit_teacher(self, teacher_id):
        teachers = db.get_all_teachers()
        t = next((x for x in teachers if x['id'] == teacher_id), None)
        if not t:
            return
        dlg = QDialog(self)
        dlg.setWindowTitle("تعديل المعلم")
        dlg.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        form = QFormLayout(dlg)
        inp_n = QLineEdit(t['name'])
        inp_p = QLineEdit(t['phone'] or "")
        inp_s = QLineEdit(t['subject'] or "")
        form.addRow("الاسم:", inp_n)
        form.addRow("الهاتف:", inp_p)
        form.addRow("المادة:", inp_s)
        btn = QPushButton("حفظ")
        btn.clicked.connect(lambda: self._save_teacher(dlg, teacher_id, inp_n.text(), inp_p.text(), inp_s.text()))
        form.addRow(btn)
        dlg.exec()

    def _save_teacher(self, dlg, tid, name, phone, subject):
        if name.strip():
            db.update_teacher(tid, name.strip(), phone.strip(), subject.strip())
            dlg.accept()
            self.refresh()

    def del_teacher(self, teacher_id):
        reply = QMessageBox.question(self, "تأكيد", "هل انت متأكد من حذف هذا المعلم؟",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            db.delete_teacher(teacher_id)
            self.refresh()


# ======================== COURSES TAB ========================

class CoursesTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        # Add Course Form
        form_box = QGroupBox("اضافة كورس جديد")
        form_layout = QFormLayout(form_box)
        self.inp_name = QLineEdit()
        self.combo_level = QComboBox()
        self.combo_teacher = QComboBox()
        self.inp_price = QDoubleSpinBox()
        self.inp_price.setMaximum(99999)
        self.inp_price.setSuffix(" جنيه")

        form_layout.addRow("اسم الكورس:", self.inp_name)
        form_layout.addRow("المستوى:", self.combo_level)
        form_layout.addRow("المعلم:", self.combo_teacher)
        form_layout.addRow("السعر الشهري:", self.inp_price)

        btn_add = QPushButton("اضافة الكورس")
        btn_add.clicked.connect(self.add_course)
        form_layout.addRow(btn_add)
        layout.addWidget(form_box)

        # Schedule section
        sched_box = QGroupBox("جدول الكورس (الايام والمواعيد)")
        sched_layout = QVBoxLayout(sched_box)

        sched_form = QHBoxLayout()
        self.combo_course_sched = QComboBox()
        self.combo_day = QComboBox()
        self.combo_day.addItems(DAYS_AR)
        self.time_edit = QTimeEdit()
        self.time_edit.setDisplayFormat("hh:mm AP")
        self.time_edit.setTime(QTime(16, 0))
        btn_add_sched = QPushButton("اضافة موعد")
        btn_add_sched.clicked.connect(self.add_schedule)

        sched_form.addWidget(QLabel("الكورس:"))
        sched_form.addWidget(self.combo_course_sched)
        sched_form.addWidget(QLabel("اليوم:"))
        sched_form.addWidget(self.combo_day)
        sched_form.addWidget(QLabel("الوقت:"))
        sched_form.addWidget(self.time_edit)
        sched_form.addWidget(btn_add_sched)
        sched_layout.addLayout(sched_form)

        self.sched_table = QTableWidget()
        self.sched_table.setColumnCount(4)
        self.sched_table.setHorizontalHeaderLabels(["#", "اليوم", "الوقت", "حذف"])
        self.sched_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        sched_layout.addWidget(self.sched_table)
        layout.addWidget(sched_box)

        # Courses table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["#", "الاسم", "المستوى", "المعلم", "السعر", "اجراءات"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)

        self.combo_course_sched.currentIndexChanged.connect(self.load_schedules)

        self.refresh()

    def refresh(self):
        # Load combos
        levels = db.get_all_levels()
        teachers = db.get_all_teachers()
        courses = db.get_all_courses()

        self.combo_level.clear()
        self.combo_level.addItem("-- اختر المستوى --", None)
        for lev in levels:
            self.combo_level.addItem(lev['name'], lev['id'])

        self.combo_teacher.clear()
        self.combo_teacher.addItem("-- اختر المعلم --", None)
        for t in teachers:
            self.combo_teacher.addItem(t['name'], t['id'])

        self.combo_course_sched.clear()
        self.combo_course_sched.addItem("-- اختر الكورس --", None)
        for c in courses:
            self.combo_course_sched.addItem(c['name'], c['id'])

        # Courses table
        self.table.setRowCount(len(courses))
        for i, c in enumerate(courses):
            self.table.setItem(i, 0, QTableWidgetItem(str(c['id'])))
            self.table.setItem(i, 1, QTableWidgetItem(c['name']))
            self.table.setItem(i, 2, QTableWidgetItem(c['level_name'] or "-"))
            self.table.setItem(i, 3, QTableWidgetItem(c['teacher_name'] or "-"))
            self.table.setItem(i, 4, QTableWidgetItem(f"{c['monthly_price']:.2f}"))

            w = QWidget()
            bl = QHBoxLayout(w)
            btn_edit = QPushButton("تعديل")
            btn_del = QPushButton("حذف")
            btn_del.setStyleSheet("background-color: #c0392b;")
            btn_edit.clicked.connect(lambda _, cid=c['id']: self.edit_course(cid))
            btn_del.clicked.connect(lambda _, cid=c['id']: self.del_course(cid))
            bl.addWidget(btn_edit)
            bl.addWidget(btn_del)
            bl.setContentsMargins(2, 2, 2, 2)
            self.table.setCellWidget(i, 5, w)

    def add_course(self):
        name = self.inp_name.text().strip()
        if not name:
            return
        level_id = self.combo_level.currentData()
        teacher_id = self.combo_teacher.currentData()
        price = self.inp_price.value()
        db.add_course(name, level_id, teacher_id, price)
        self.inp_name.clear()
        self.inp_price.setValue(0)
        self.refresh()

    def edit_course(self, course_id):
        course = db.get_course_by_id(course_id)
        if not course:
            return
        dlg = QDialog(self)
        dlg.setWindowTitle("تعديل الكورس")
        dlg.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        form = QFormLayout(dlg)

        inp_n = QLineEdit(course['name'])
        combo_l = QComboBox()
        combo_t = QComboBox()
        inp_p = QDoubleSpinBox()
        inp_p.setMaximum(99999)
        inp_p.setValue(course['monthly_price'])

        combo_l.addItem("-- اختر --", None)
        for lev in db.get_all_levels():
            combo_l.addItem(lev['name'], lev['id'])
            if lev['id'] == course['level_id']:
                combo_l.setCurrentIndex(combo_l.count() - 1)

        combo_t.addItem("-- اختر --", None)
        for t in db.get_all_teachers():
            combo_t.addItem(t['name'], t['id'])
            if t['id'] == course['teacher_id']:
                combo_t.setCurrentIndex(combo_t.count() - 1)

        form.addRow("الاسم:", inp_n)
        form.addRow("المستوى:", combo_l)
        form.addRow("المعلم:", combo_t)
        form.addRow("السعر:", inp_p)

        btn = QPushButton("حفظ")
        btn.clicked.connect(lambda: self._save_course(dlg, course_id, inp_n.text(),
                                                       combo_l.currentData(), combo_t.currentData(), inp_p.value()))
        form.addRow(btn)
        dlg.exec()

    def _save_course(self, dlg, cid, name, lid, tid, price):
        if name.strip():
            db.update_course(cid, name.strip(), lid, tid, price)
            dlg.accept()
            self.refresh()

    def del_course(self, course_id):
        reply = QMessageBox.question(self, "تأكيد", "هل انت متأكد من حذف هذا الكورس؟ سيتم حذف كل المجموعات المرتبطة.",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            db.delete_course(course_id)
            self.refresh()

    def add_schedule(self):
        course_id = self.combo_course_sched.currentData()
        if course_id is None:
            QMessageBox.warning(self, "خطأ", "اختر كورس اولا")
            return
        day = self.combo_day.currentText()
        time_str = self.time_edit.time().toString("hh:mm AP")
        db.add_course_schedule(course_id, day, time_str)
        self.load_schedules()

    def load_schedules(self):
        course_id = self.combo_course_sched.currentData()
        if course_id is None:
            self.sched_table.setRowCount(0)
            return
        schedules = db.get_course_schedules(course_id)
        self.sched_table.setRowCount(len(schedules))
        for i, s in enumerate(schedules):
            self.sched_table.setItem(i, 0, QTableWidgetItem(str(s['id'])))
            self.sched_table.setItem(i, 1, QTableWidgetItem(s['day']))
            self.sched_table.setItem(i, 2, QTableWidgetItem(s['time']))
            btn_del = QPushButton("حذف")
            btn_del.setStyleSheet("background-color: #c0392b;")
            btn_del.clicked.connect(lambda _, sid=s['id']: self._del_schedule(sid))
            self.sched_table.setCellWidget(i, 3, btn_del)

    def _del_schedule(self, schedule_id):
        db.delete_course_schedule(schedule_id)
        self.load_schedules()


# ======================== GROUPS TAB ========================

class GroupsTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        # Add Group Form
        form_box = QGroupBox("اضافة مجموعة جديدة")
        form_layout = QFormLayout(form_box)

        self.inp_name = QLineEdit()
        self.combo_course = QComboBox()
        self.combo_course.currentIndexChanged.connect(self._on_course_changed)

        form_layout.addRow("اسم المجموعة:", self.inp_name)
        form_layout.addRow("الكورس:", self.combo_course)

        # Checkboxes for days - populated from course schedule
        self.days_group = QGroupBox("اختر ايام الحضور من جدول الكورس")
        self.days_layout = QVBoxLayout(self.days_group)
        self.day_checkboxes = []
        form_layout.addRow(self.days_group)

        btn_add = QPushButton("اضافة المجموعة")
        btn_add.clicked.connect(self.add_group)
        form_layout.addRow(btn_add)
        layout.addWidget(form_box)

        # Groups table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["#", "الاسم", "الكورس", "الايام", "اجراءات"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)

        self.refresh()

    def refresh(self):
        courses = db.get_all_courses()
        self.combo_course.blockSignals(True)
        self.combo_course.clear()
        self.combo_course.addItem("-- اختر الكورس --", None)
        for c in courses:
            self.combo_course.addItem(c['name'], c['id'])
        self.combo_course.blockSignals(False)
        self._on_course_changed()

        groups = db.get_all_groups()
        self.table.setRowCount(len(groups))
        for i, g in enumerate(groups):
            self.table.setItem(i, 0, QTableWidgetItem(str(g['id'])))
            self.table.setItem(i, 1, QTableWidgetItem(g['name']))
            self.table.setItem(i, 2, QTableWidgetItem(g['course_name'] or "-"))
            try:
                days = json.loads(g['selected_days_json'])
                days_str = " | ".join(days)
            except (json.JSONDecodeError, TypeError):
                days_str = "-"
            self.table.setItem(i, 3, QTableWidgetItem(days_str))

            w = QWidget()
            bl = QHBoxLayout(w)
            btn_edit = QPushButton("تعديل")
            btn_del = QPushButton("حذف")
            btn_del.setStyleSheet("background-color: #c0392b;")
            btn_edit.clicked.connect(lambda _, gid=g['id']: self.edit_group(gid))
            btn_del.clicked.connect(lambda _, gid=g['id']: self.del_group(gid))
            bl.addWidget(btn_edit)
            bl.addWidget(btn_del)
            bl.setContentsMargins(2, 2, 2, 2)
            self.table.setCellWidget(i, 4, w)

    def _on_course_changed(self):
        # Clear existing checkboxes
        for cb in self.day_checkboxes:
            self.days_layout.removeWidget(cb)
            cb.deleteLater()
        self.day_checkboxes.clear()

        course_id = self.combo_course.currentData()
        if course_id is None:
            return

        schedules = db.get_course_schedules(course_id)
        for s in schedules:
            label = f"{s['day']} - {s['time']}"
            cb = QCheckBox(label)
            cb.setProperty("day_name", s['day'])
            self.day_checkboxes.append(cb)
            self.days_layout.addWidget(cb)

    def add_group(self):
        name = self.inp_name.text().strip()
        course_id = self.combo_course.currentData()
        if not name or course_id is None:
            QMessageBox.warning(self, "خطأ", "ادخل اسم المجموعة واختر الكورس")
            return

        selected_days = []
        for cb in self.day_checkboxes:
            if cb.isChecked():
                selected_days.append(cb.property("day_name"))

        if not selected_days:
            QMessageBox.warning(self, "خطأ", "اختر يوم واحد على الاقل")
            return

        db.add_group(name, course_id, json.dumps(selected_days, ensure_ascii=False))
        self.inp_name.clear()
        self.refresh()

    def edit_group(self, group_id):
        group = db.get_group_by_id(group_id)
        if not group:
            return

        dlg = QDialog(self)
        dlg.setWindowTitle("تعديل المجموعة")
        dlg.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        dlg.setMinimumWidth(400)
        form = QFormLayout(dlg)

        inp_n = QLineEdit(group['name'])
        combo_c = QComboBox()
        courses = db.get_all_courses()
        combo_c.addItem("-- اختر --", None)
        for c in courses:
            combo_c.addItem(c['name'], c['id'])
            if c['id'] == group['course_id']:
                combo_c.setCurrentIndex(combo_c.count() - 1)

        form.addRow("الاسم:", inp_n)
        form.addRow("الكورس:", combo_c)

        # Checkboxes
        days_box = QGroupBox("الايام")
        days_lay = QVBoxLayout(days_box)
        edit_cbs = []

        try:
            current_days = json.loads(group['selected_days_json'])
        except (json.JSONDecodeError, TypeError):
            current_days = []

        def load_edit_schedules():
            for cb in edit_cbs:
                days_lay.removeWidget(cb)
                cb.deleteLater()
            edit_cbs.clear()
            cid = combo_c.currentData()
            if cid is None:
                return
            scheds = db.get_course_schedules(cid)
            for s in scheds:
                label = f"{s['day']} - {s['time']}"
                cb = QCheckBox(label)
                cb.setProperty("day_name", s['day'])
                if s['day'] in current_days:
                    cb.setChecked(True)
                edit_cbs.append(cb)
                days_lay.addWidget(cb)

        combo_c.currentIndexChanged.connect(load_edit_schedules)
        load_edit_schedules()
        form.addRow(days_box)

        btn = QPushButton("حفظ")
        btn.clicked.connect(lambda: self._save_group(dlg, group_id, inp_n.text(),
                                                      combo_c.currentData(), edit_cbs))
        form.addRow(btn)
        dlg.exec()

    def _save_group(self, dlg, gid, name, course_id, cbs):
        if not name.strip() or course_id is None:
            return
        selected = [cb.property("day_name") for cb in cbs if cb.isChecked()]
        if not selected:
            QMessageBox.warning(self, "خطأ", "اختر يوم واحد على الاقل")
            return
        db.update_group(gid, name.strip(), course_id, json.dumps(selected, ensure_ascii=False))
        dlg.accept()
        self.refresh()

    def del_group(self, group_id):
        reply = QMessageBox.question(self, "تأكيد", "هل انت متأكد من حذف هذه المجموعة؟",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            db.delete_group(group_id)
            self.refresh()
