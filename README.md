# Maestro ERP - Educational Center Management System

A professional Educational Center Management System built with **PyQt6** and **SQLite3**, featuring a dark modern UI, full Arabic (RTL) support, and a strict accounting engine.

## Features

- **Students Dashboard**: Batch actions (transfer, delete, bulk pay), debt tracking, instant search
- **Attendance System**: Smart attendance showing only groups scheduled for today, color-coded calendar view
- **Financial Engine**: Income/expense tracking, student ledger, partial payments, total center debts
- **Invoice Engine**: Professional PDF receipts with Arabic support via `reportlab`
- **Inventory & Sales**: Stock management, sell to students with automatic finance/ledger integration
- **Settings & Scheduling**: Manage levels, teachers, courses, schedules, and groups with checkbox day selection

## Architecture

| File | Purpose |
|------|---------|
| `main.py` | Application entry point, dark theme, sidebar navigation |
| `database_manager.py` | SQLite database layer with Foreign Keys |
| `ui_students.py` | Students dashboard, attendance, profile/calendar |
| `ui_finances.py` | Finance vault, transaction management |
| `ui_inventory.py` | Inventory management, sales |
| `ui_settings.py` | Levels, teachers, courses, schedules, groups (checkbox logic) |
| `invoice_engine.py` | PDF invoice generation |

## Database Schema

- **Levels** - Course levels
- **Teachers** - Name, phone, subject
- **Courses** - Linked to level and teacher, with monthly price
- **Course Schedules** - Global day/time schedules per course
- **Groups** - Linked to course, with selected days (JSON checkboxes from course schedule)
- **Students** - Linked to group, with status
- **Subscriptions** - Student billing: total required, paid amount, due date
- **Finance** - Income/expense transactions
- **Student Ledger** - Per-student financial statement (debit/credit/balance)
- **Attendance** - Daily records (present/absent/charged absence)
- **Inventory** - Items with stock and price

## Installation

```bash
pip install -r requirements.txt
```

## Running

```bash
python main.py
```

## Requirements

- Python 3.10+
- PyQt6
- reportlab (for PDF invoices)
- arabic-reshaper & python-bidi (for Arabic PDF rendering)
