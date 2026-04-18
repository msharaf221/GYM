"""
utils.py - Utility functions: receipt generation, formatters, helpers.
"""

import os
from datetime import datetime


def format_currency(amount: float) -> str:
    """Format amount as Egyptian Pounds."""
    return f"{amount:,.2f} ج.م"


def format_date(dt_str: str) -> str:
    """Format ISO datetime string to readable Arabic-friendly format."""
    if not dt_str:
        return ""
    try:
        dt = datetime.fromisoformat(dt_str)
        return dt.strftime("%Y/%m/%d %H:%M")
    except (ValueError, TypeError):
        return dt_str


def generate_sale_receipt(item_name, quantity, unit_price, total, receipt_id=""):
    """Generate a text receipt for a sale."""
    now = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    lines = [
        "=" * 40,
        "       إيصال بيع - موبايل شوب",
        "=" * 40,
        f"  رقم الإيصال: {receipt_id}",
        f"  التاريخ: {now}",
        "-" * 40,
        f"  المنتج: {item_name}",
        f"  الكمية: {quantity}",
        f"  سعر الوحدة: {format_currency(unit_price)}",
        f"  الإجمالي: {format_currency(total)}",
        "-" * 40,
        "       شكراً لتعاملكم معنا!",
        "=" * 40,
    ]
    return "\n".join(lines)


def generate_maintenance_receipt(customer_name, device_type, issue, service_fee, spare_cost, receipt_id=""):
    """Generate a text receipt for maintenance."""
    now = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    total = service_fee
    net = service_fee - spare_cost
    lines = [
        "=" * 40,
        "     إيصال صيانة - موبايل شوب",
        "=" * 40,
        f"  رقم الإيصال: {receipt_id}",
        f"  التاريخ: {now}",
        "-" * 40,
        f"  العميل: {customer_name}",
        f"  الجهاز: {device_type}",
        f"  المشكلة: {issue}",
        "-" * 40,
        f"  تكلفة قطع الغيار: {format_currency(spare_cost)}",
        f"  رسوم الخدمة: {format_currency(service_fee)}",
        f"  الإجمالي المطلوب: {format_currency(total)}",
        "-" * 40,
        "       شكراً لتعاملكم معنا!",
        "=" * 40,
    ]
    return "\n".join(lines)


def generate_wallet_receipt(wallet_name, txn_type, amount, client_phone, system_fee, commission, receipt_id=""):
    """Generate a text receipt for wallet transaction."""
    now = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    type_map = {"deposit": "إيداع", "withdraw": "سحب", "transfer": "تحويل"}
    lines = [
        "=" * 40,
        "   إيصال محفظة رقمية - موبايل شوب",
        "=" * 40,
        f"  رقم الإيصال: {receipt_id}",
        f"  التاريخ: {now}",
        "-" * 40,
        f"  المحفظة: {wallet_name}",
        f"  نوع العملية: {type_map.get(txn_type, txn_type)}",
        f"  المبلغ: {format_currency(amount)}",
        f"  رقم العميل: {client_phone}",
        f"  رسوم النظام: {format_currency(system_fee)}",
        f"  عمولة المحل: {format_currency(commission)}",
        "-" * 40,
        "       شكراً لتعاملكم معنا!",
        "=" * 40,
    ]
    return "\n".join(lines)


def save_receipt_to_file(receipt_text: str, filename: str = None) -> str:
    """Save receipt to a text file in receipts directory."""
    receipts_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "receipts")
    os.makedirs(receipts_dir, exist_ok=True)
    if not filename:
        filename = f"receipt_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    filepath = os.path.join(receipts_dir, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(receipt_text)
    return filepath
