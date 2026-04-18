# Mobile Shop & Digital Wallet Management System

A professional desktop application for managing a Mobile Shop built with **Python**, **PyQt6**, and **SQLite3**. The system handles Inventory (Accessories), Maintenance (Repairs), and Digital Wallet transactions (Vodafone Cash, InstaPay, Fawry) with strict accounting integrity and monthly limits.

## Features

### Inventory Management (Accessories)
- Dynamic item identification: Manual Name, Manual Code, or Barcode Scanner
- Auto-generated unique Barcode/SKU if not provided
- Real-time stock deduction on sales with "Low Stock Alerts"
- Quick price update feature for market volatility
- Full CRUD with search and category filtering

### Maintenance Hub (Repairs)
- Lifecycle tracking: Received -> In-Progress -> Ready -> Delivered
- Profit calculation: Spare Part Cost vs. Service Fee
- Automatic spare part deduction from inventory
- Net profit recording in finance vault on delivery

### Digital Wallet & Remittance
- Multi-wallet registry (Vodafone Cash, InstaPay, Orange Money, Fawry, etc.)
- Monthly Transaction Limit tracker with visual alerts at 80% threshold
- Commission logic: Amount, Client Number, System Fee, Shop Commission
- Limit exceeded warnings with confirmation

### Multi-Vault Accounting
- Separated vaults: Physical Cash, Bank/InstaPay, Digital Wallet Balances
- Every transaction generates a Transaction ID linked to the daily shift
- Advanced dashboard with filtered profits: Accessories | Maintenance | Wallet Commissions
- Inter-vault transfers and manual adjustments (Admin only)

### Security
- Multi-level login: Admin / Staff
- Staff restricted from profit viewing and deletion
- Confirmation dialogs for all critical actions

### Receipt Generation
- Text-based receipts for sales, maintenance, and wallet transactions
- Saved to local `receipts/` directory

## Project Structure

```
main.py              # Entry point, login, main window, sidebar navigation
database.py          # SQLite3 database layer, migrations, all DB operations
ui_inventory.py      # Inventory/Accessories management UI
ui_maintenance.py    # Maintenance/Repairs management UI
ui_wallets.py        # Digital Wallet management UI
ui_accounting.py     # Multi-vault accounting and dashboard UI
styles.py            # Modern Dark Mode stylesheet
utils.py             # Receipt generation, formatters, helpers
requirements.txt     # Python dependencies
```

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

## Default Login

- **Username:** `admin`
- **Password:** `Muhamed@3512139M`
- **Role:** Admin (full access)

## Technical Details

- **Language:** Python 3.10+
- **UI Framework:** PyQt6 with RTL (Right-to-Left) Arabic support
- **Database:** SQLite3 with Foreign Keys enabled, WAL journal mode
- **Design:** Modern Dark Mode palette with sidebar navigation
- **Architecture:** Modular file structure with separated concerns

## UI Language

The entire UI is in **Arabic** with full RTL layout support.
