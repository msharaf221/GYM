import sys
import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QLabel,
    QHeaderView, QComboBox, QTabWidget, QMessageBox, QDialog, QFormLayout
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QBrush
from database import DatabaseManager
from invoicing import InvoiceGenerator
from exports import ExcelExporter

class StudentDashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = DatabaseManager('maestro_center.db')
        self.setWindowTitle("Maestro Center Manager - Dashboard")
        self.setMinimumSize(1000, 600)
        self.init_ui()
        self.load_students()

    def init_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)

        # Dashboard Tab
        self.dashboard_tab = QWidget()
        self.tabs.addTab(self.dashboard_tab, "Dashboard")
        self.setup_dashboard_tab()

        # Attendance Tab
        self.attendance_tab = QWidget()
        self.tabs.addTab(self.attendance_tab, "Attendance")
        self.setup_attendance_tab()

        # Books Tab (Owner Only)
        self.books_tab = QWidget()
        self.tabs.addTab(self.books_tab, "Books (Owner Only)")
        self.setup_books_tab()

        # Payroll Tab
        self.payroll_tab = QWidget()
        self.tabs.addTab(self.payroll_tab, "Payroll")
        self.setup_payroll_tab()

        # Expenses Tab
        self.expenses_tab = QWidget()
        self.tabs.addTab(self.expenses_tab, "Expenses")
        self.setup_expenses_tab()

        # Retention Tab
        self.retention_tab = QWidget()
        self.tabs.addTab(self.retention_tab, "Retention Alarm")
        self.setup_retention_tab()

        # Families Tab
        self.families_tab = QWidget()
        self.tabs.addTab(self.families_tab, "Sibling Linker")
        self.setup_families_tab()

    def setup_dashboard_tab(self):
        layout = QVBoxLayout(self.dashboard_tab)
        # Header/Search
        header_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by Name, Phone, or Barcode...")
        self.search_input.textChanged.connect(self.load_students)
        header_layout.addWidget(QLabel("Search:"))
        header_layout.addWidget(self.search_input)

        self.record_payment_btn = QPushButton("Record Payment / Invoice")
        self.record_payment_btn.clicked.connect(self.show_payment_dialog)
        header_layout.addWidget(self.record_payment_btn)

        self.export_btn = QPushButton("Export Students")
        self.export_btn.clicked.connect(self.export_students_xlsx)
        header_layout.addWidget(self.export_btn)

        layout.addLayout(header_layout)

        # Student Table
        self.student_table = QTableWidget()
        self.student_table.setColumnCount(6)
        self.student_table.setHorizontalHeaderLabels([
            "ID", "Status", "Name", "Phone", "Grade", "Barcode"
        ])
        self.student_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.student_table)

        # Legend
        self.legend_layout = QHBoxLayout()
        self.legend_layout.addWidget(QLabel("Traffic Light: "))
        self.add_legend_item(self.legend_layout, "Green: Paid", QColor("green"))
        self.add_legend_item(self.legend_layout, "Red: Debt", QColor("red"))
        self.add_legend_item(self.legend_layout, "Yellow: Pending", QColor("yellow"))
        self.add_legend_item(self.legend_layout, "Grey: Inactive", QColor("grey"))
        layout.addLayout(self.legend_layout)

    def show_payment_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Record Payment")
        d_layout = QFormLayout(dialog)

        s_id_input = QLineEdit()
        amount_input = QLineEdit()
        paid_input = QLineEdit()
        desc_input = QLineEdit("Monthly Fee")

        d_layout.addRow("Student ID:", s_id_input)
        d_layout.addRow("Total Amount:", amount_input)
        d_layout.addRow("Paid Amount:", paid_input)
        d_layout.addRow("Item Description:", desc_input)

        submit_btn = QPushButton("Submit")
        d_layout.addRow(submit_btn)

        def process_payment():
            try:
                s_id = int(s_id_input.text())
                total = float(amount_input.text())
                paid = float(paid_input.text())
                desc = desc_input.text()

                with self.db.get_connection() as conn:
                    cursor = conn.cursor()
                    # Get previous debt
                    cursor.execute("SELECT SUM(total_amount) - SUM(paid_amount) FROM invoices WHERE student_id = ?", (s_id,))
                    res = cursor.fetchone()
                    prev_debt = res[0] if res and res[0] is not None else 0.0

                    date_str = datetime.date.today().isoformat()
                    cursor.execute("INSERT INTO invoices (student_id, total_amount, paid_amount, previous_debt, date) VALUES (?, ?, ?, ?, ?)",
                                   (s_id, total, paid, prev_debt, date_str))
                    inv_id = cursor.lastrowid
                    cursor.execute("INSERT INTO invoice_items (invoice_id, item_type, amount) VALUES (?, ?, ?)", (inv_id, desc, total))
                    conn.commit()

                    # Generate PDF
                    cursor.execute("SELECT name FROM students WHERE id = ?", (s_id,))
                    s_name = cursor.fetchone()[0]

                    ig = InvoiceGenerator()
                    ig.generate_receipt(f"invoice_{inv_id}.pdf", s_name, [(desc, total)], total, paid, prev_debt, date_str)

                    QMessageBox.information(self, "Success", f"Invoice generated: invoice_{inv_id}.pdf")
                    dialog.accept()
                    self.load_students()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Invalid input: {str(e)}")

        submit_btn.clicked.connect(process_payment)
        dialog.exec()

    def export_students_xlsx(self):
        exporter = ExcelExporter(self.db)
        fname = exporter.export_students()
        QMessageBox.information(self, "Success", f"Report exported to {fname}")

    def setup_attendance_tab(self):
        layout = QVBoxLayout(self.attendance_tab)

        # Controls
        controls_layout = QHBoxLayout()
        self.grade_filter = QComboBox()
        self.grade_filter.addItem("Select Grade")
        self.grade_filter.currentIndexChanged.connect(self.load_attendance_grid)
        controls_layout.addWidget(QLabel("Grade:"))
        controls_layout.addWidget(self.grade_filter)
        layout.addLayout(controls_layout)

        # Attendance Grid
        self.attendance_grid = QTableWidget()
        layout.addWidget(self.attendance_grid)

        # Legend for Attendance
        attn_legend_layout = QHBoxLayout()
        attn_legend_layout.addWidget(QLabel("Attendance Grid: "))
        self.add_legend_item(attn_legend_layout, "Green: Present", QColor("green"))
        self.add_legend_item(attn_legend_layout, "Red: Absent", QColor("red"))
        self.add_legend_item(attn_legend_layout, "Grey: Canceled/Not Started", QColor("grey"))
        layout.addLayout(attn_legend_layout)

        self.load_grades_filter()

    def load_grades_filter(self):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name FROM grades")
            for g_id, name in cursor.fetchall():
                self.grade_filter.addItem(name, g_id)

    def load_attendance_grid(self):
        grade_id = self.grade_filter.currentData()
        if not grade_id:
            return

        with self.db.get_connection() as conn:
            cursor = conn.cursor()

            # Get students in this grade
            cursor.execute("SELECT id, name FROM students WHERE grade_id = ?", (grade_id,))
            students = cursor.fetchall()

            # Get sessions for this grade
            cursor.execute("SELECT id, session_date FROM sessions WHERE grade_id = ? ORDER BY session_date", (grade_id,))
            sessions = cursor.fetchall()

            self.attendance_grid.setRowCount(len(students))
            self.attendance_grid.setColumnCount(len(sessions) + 1)

            headers = ["Student Name"] + [s[1] for s in sessions]
            self.attendance_grid.setHorizontalHeaderLabels(headers)

            for r_idx, (s_id, s_name) in enumerate(students):
                self.attendance_grid.setItem(r_idx, 0, QTableWidgetItem(s_name))

                for c_idx, (sess_id, _) in enumerate(sessions):
                    cursor.execute("SELECT status FROM attendance WHERE student_id = ? AND session_id = ?", (s_id, sess_id))
                    res = cursor.fetchone()
                    status = res[0] if res else None

                    item = QTableWidgetItem()
                    if status == "Present":
                        item.setBackground(QBrush(QColor("green")))
                    elif status == "Absent":
                        item.setBackground(QBrush(QColor("red")))
                    else:
                        item.setBackground(QBrush(QColor("grey")))

                    self.attendance_grid.setItem(r_idx, c_idx + 1, item)

    def setup_books_tab(self):
        layout = QVBoxLayout(self.books_tab)

        # Forms
        form_layout = QHBoxLayout()
        self.book_title = QLineEdit()
        self.book_title.setPlaceholderText("Book Title")
        self.book_price = QLineEdit()
        self.book_price.setPlaceholderText("Price")
        self.book_stock = QLineEdit()
        self.book_stock.setPlaceholderText("Stock Qty")
        add_book_btn = QPushButton("Add/Update Book")
        add_book_btn.clicked.connect(self.add_book)

        form_layout.addWidget(self.book_title)
        form_layout.addWidget(self.book_price)
        form_layout.addWidget(self.book_stock)
        form_layout.addWidget(add_book_btn)
        layout.addLayout(form_layout)

        # Books Table
        self.books_table = QTableWidget()
        self.books_table.setColumnCount(4)
        self.books_table.setHorizontalHeaderLabels(["ID", "Title", "Price", "Stock"])
        self.books_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.books_table)

        # Revenue Info
        self.revenue_label = QLabel("Book Sales Revenue: $0.00")
        layout.addWidget(self.revenue_label)

        self.load_books()
        self.update_book_revenue()

    def load_books(self):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, title, price, stock_quantity FROM books")
            books = cursor.fetchall()
            self.books_table.setRowCount(len(books))
            for row, book in enumerate(books):
                for col, val in enumerate(book):
                    self.books_table.setItem(row, col, QTableWidgetItem(str(val)))

    def add_book(self):
        try:
            title = self.book_title.text()
            if not title: raise ValueError("Title required")
            price = float(self.book_price.text() or 0)
            stock = int(self.book_stock.text() or 0)

            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO books (title, price, stock_quantity) ON CONFLICT(title) DO UPDATE SET price=excluded.price, stock_quantity=excluded.stock_quantity", (title, price, stock))
                conn.commit()
        except Exception as e:
            QMessageBox.warning(self, "Input Error", f"Could not add book: {str(e)}")

        self.load_books()
        self.book_title.clear()
        self.book_price.clear()
        self.book_stock.clear()

    def update_book_revenue(self):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT SUM(amount) FROM invoice_items WHERE item_type = 'Book'")
            res = cursor.fetchone()
            revenue = res[0] if res and res[0] is not None else 0.0
            self.revenue_label.setText(f"Book Sales Revenue: ${revenue:.2f}")

    def setup_payroll_tab(self):
        layout = QVBoxLayout(self.payroll_tab)

        controls = QHBoxLayout()
        self.teacher_select = QComboBox()
        self.teacher_select.addItem("Select Teacher")
        self.teacher_select.currentIndexChanged.connect(self.calculate_payroll)
        controls.addWidget(QLabel("Teacher:"))
        controls.addWidget(self.teacher_select)
        layout.addLayout(controls)

        self.payroll_table = QTableWidget()
        self.payroll_table.setColumnCount(4)
        self.payroll_table.setHorizontalHeaderLabels(["Session Date", "Student Count", "Session Price", "Teacher Pay"])
        self.payroll_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.payroll_table)

        self.total_pay_label = QLabel("Total Payroll: $0.00")
        layout.addWidget(self.total_pay_label)

        self.load_teachers_filter()

    def load_teachers_filter(self):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name FROM teachers")
            for t_id, name in cursor.fetchall():
                self.teacher_select.addItem(name, t_id)

    def calculate_payroll(self):
        teacher_id = self.teacher_select.currentData()
        if not teacher_id:
            return

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            # Get teacher commission
            cursor.execute("SELECT commission_rate FROM teachers WHERE id = ?", (teacher_id,))
            commission_rate = cursor.fetchone()[0] or 0.0

            # Get sessions by this teacher
            cursor.execute("SELECT id, session_date, session_price FROM sessions WHERE teacher_id = ?", (teacher_id,))
            sessions = cursor.fetchall()

            self.payroll_table.setRowCount(len(sessions))
            total_payroll = 0

            for row, sess in enumerate(sessions):
                sess_id, date, price = sess
                # Count students in this session
                cursor.execute("SELECT COUNT(*) FROM attendance WHERE session_id = ? AND status = 'Present'", (sess_id,))
                student_count = cursor.fetchone()[0]

                # Pay = (Count * Price) * (1 - commission_rate)
                # Formula: (Students Count × Session Price) - Center Commission %
                sess_total = student_count * price
                teacher_pay = sess_total * (1 - (commission_rate / 100.0))
                total_payroll += teacher_pay

                self.payroll_table.setItem(row, 0, QTableWidgetItem(date))
                self.payroll_table.setItem(row, 1, QTableWidgetItem(str(student_count)))
                self.payroll_table.setItem(row, 2, QTableWidgetItem(f"{price:.2f}"))
                self.payroll_table.setItem(row, 3, QTableWidgetItem(f"{teacher_pay:.2f}"))

            self.total_pay_label.setText(f"Total Payroll: ${total_payroll:.2f}")

    def setup_expenses_tab(self):
        layout = QVBoxLayout(self.expenses_tab)

        form_layout = QHBoxLayout()
        self.expense_desc = QLineEdit()
        self.expense_desc.setPlaceholderText("Description")
        self.expense_amount = QLineEdit()
        self.expense_amount.setPlaceholderText("Amount")
        self.expense_category = QComboBox()
        self.expense_category.addItems(["Rent", "Electricity", "Salary", "Internet", "Others"])
        self.expense_date = QLineEdit()
        self.expense_date.setPlaceholderText("YYYY-MM-DD")
        add_expense_btn = QPushButton("Add Expense")
        add_expense_btn.clicked.connect(self.add_expense)

        form_layout.addWidget(self.expense_desc)
        form_layout.addWidget(self.expense_amount)
        form_layout.addWidget(self.expense_category)
        form_layout.addWidget(self.expense_date)
        form_layout.addWidget(add_expense_btn)
        layout.addLayout(form_layout)

        self.expenses_table = QTableWidget()
        self.expenses_table.setColumnCount(5)
        self.expenses_table.setHorizontalHeaderLabels(["ID", "Date", "Category", "Description", "Amount"])
        self.expenses_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.expenses_table)

        self.total_expense_label = QLabel("Total Expenses: $0.00")
        layout.addWidget(self.total_expense_label)

        self.load_expenses()

    def add_expense(self):
        try:
            desc = self.expense_desc.text()
            amount = float(self.expense_amount.text() or 0)
            category = self.expense_category.currentText()
            date = self.expense_date.text()
            if not desc: raise ValueError("Description required")

            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO expenses (description, amount, category, date) VALUES (?, ?, ?, ?)", (desc, amount, category, date))
                conn.commit()
        except Exception as e:
            QMessageBox.warning(self, "Input Error", f"Could not add expense: {str(e)}")

        self.load_expenses()
        self.expense_desc.clear()
        self.expense_amount.clear()
        self.expense_date.clear()

    def load_expenses(self):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, date, category, description, amount FROM expenses ORDER BY date DESC")
            expenses = cursor.fetchall()
            self.expenses_table.setRowCount(len(expenses))
            total_expenses = 0
            for row, exp in enumerate(expenses):
                total_expenses += exp[4]
                for col, val in enumerate(exp):
                    self.expenses_table.setItem(row, col, QTableWidgetItem(str(val)))
            self.total_expense_label.setText(f"Total Expenses: ${total_expenses:.2f}")

    def setup_retention_tab(self):
        layout = QVBoxLayout(self.retention_tab)
        layout.addWidget(QLabel("Students who missed 2+ consecutive sessions:"))

        self.retention_table = QTableWidget()
        self.retention_table.setColumnCount(3)
        self.retention_table.setHorizontalHeaderLabels(["Student ID", "Name", "Consecutive Absences"])
        self.retention_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.retention_table)

        refresh_btn = QPushButton("Refresh Retention Alarm")
        refresh_btn.clicked.connect(self.load_retention_alarm)
        layout.addWidget(refresh_btn)

        self.load_retention_alarm()

    def load_retention_alarm(self):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            # For each student, get their last N sessions' attendance in reverse order
            cursor.execute("SELECT id, name FROM students WHERE status = 'Active'")
            students = cursor.fetchall()

            alarm_list = []
            for s_id, s_name in students:
                # Get last sessions for this student's grade
                cursor.execute("""
                    SELECT a.status
                    FROM attendance a
                    JOIN sessions s ON a.session_id = s.id
                    WHERE a.student_id = ?
                    ORDER BY s.session_date DESC
                    LIMIT 10
                """, (s_id,))
                statuses = [row[0] for row in cursor.fetchall()]

                consecutive_absences = 0
                for status in statuses:
                    if status == 'Absent':
                        consecutive_absences += 1
                    else:
                        break # Only consecutive from the latest

                if consecutive_absences >= 2:
                    alarm_list.append((s_id, s_name, consecutive_absences))

            self.retention_table.setRowCount(len(alarm_list))
            for row, data in enumerate(alarm_list):
                for col, val in enumerate(data):
                    self.retention_table.setItem(row, col, QTableWidgetItem(str(val)))

    def setup_families_tab(self):
        layout = QVBoxLayout(self.families_tab)

        form_layout = QHBoxLayout()
        self.family_name = QLineEdit()
        self.family_name.setPlaceholderText("Family Name")
        self.family_discount = QLineEdit()
        self.family_discount.setPlaceholderText("Discount Rate %")
        add_family_btn = QPushButton("Add Family")
        add_family_btn.clicked.connect(self.add_family)
        form_layout.addWidget(self.family_name)
        form_layout.addWidget(self.family_discount)
        form_layout.addWidget(add_family_btn)
        layout.addLayout(form_layout)

        self.families_table = QTableWidget()
        self.families_table.setColumnCount(3)
        self.families_table.setHorizontalHeaderLabels(["ID", "Family Name", "Discount %"])
        self.families_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.families_table)

        self.load_families()

    def add_family(self):
        try:
            name = self.family_name.text()
            if not name: raise ValueError("Family name required")
            discount = float(self.family_discount.text() or 0)
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO families (family_name, discount_rate) VALUES (?, ?)", (name, discount))
                conn.commit()
        except Exception as e:
            QMessageBox.warning(self, "Input Error", f"Could not add family: {str(e)}")
        self.load_families()
        self.family_name.clear()
        self.family_discount.clear()

    def load_families(self):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, family_name, discount_rate FROM families")
            families = cursor.fetchall()
            self.families_table.setRowCount(len(families))
            for row, fam in enumerate(families):
                for col, val in enumerate(fam):
                    self.families_table.setItem(row, col, QTableWidgetItem(str(val)))

    def get_sibling_discount(self, student_id):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT f.discount_rate
                FROM families f
                JOIN students s ON s.family_id = f.id
                WHERE s.id = ?
            """, (student_id,))
            res = cursor.fetchone()
            return res[0] if res else 0.0

    def add_legend_item(self, layout, text, color):
        label = QLabel(text)
        label.setStyleSheet(f"background-color: {color.name()}; padding: 2px 5px; color: {'black' if color == QColor('yellow') else 'white'};")
        layout.addWidget(label)


    def load_students(self):
        search_text = self.search_input.text()
        query = "SELECT s.id, s.name, s.phone, s.barcode, g.name, s.status FROM students s LEFT JOIN grades g ON s.grade_id = g.id"

        params = []
        if search_text:
            query += " WHERE s.name LIKE ? OR s.phone LIKE ? OR s.barcode LIKE ?"
            params = [f"%{search_text}%", f"%{search_text}%", f"%{search_text}%"]

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            students = cursor.fetchall()

            self.student_table.setRowCount(len(students))
            for row_idx, student in enumerate(students):
                s_id, name, phone, barcode, grade, status = student

                # Get payment status for traffic light
                payment_color = self.get_payment_status_color(s_id, status)

                status_item = QTableWidgetItem()
                status_item.setBackground(QBrush(payment_color))

                self.student_table.setItem(row_idx, 0, QTableWidgetItem(str(s_id)))
                self.student_table.setItem(row_idx, 1, status_item)
                self.student_table.setItem(row_idx, 2, QTableWidgetItem(name))
                self.student_table.setItem(row_idx, 3, QTableWidgetItem(phone))
                self.student_table.setItem(row_idx, 4, QTableWidgetItem(grade if grade else "No Grade"))
                self.student_table.setItem(row_idx, 5, QTableWidgetItem(barcode))

    def get_payment_status_color(self, student_id, student_status):
        if student_status != "Active":
            return QColor("grey")

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            # Logic: Check total invoiced vs total paid
            cursor.execute("SELECT SUM(total_amount), SUM(paid_amount) FROM invoices WHERE student_id = ?", (student_id,))
            res = cursor.fetchone()
            total_invoiced, total_paid = res if res and res[0] is not None else (0, 0)

            if total_invoiced == 0:
                return QColor("yellow") # Pending (No invoices yet)
            elif total_paid >= total_invoiced:
                return QColor("green")
            else:
                return QColor("red")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = StudentDashboard()
    window.show()
    sys.exit(app.exec())
