# -*- coding: utf-8 -*-
"""
Tiện ích xử lý dữ liệu chung cho các parser.
"""

import re
import pandas as pd
import numpy as np


def clean_number(val):
    """
    Chuyển đổi chuỗi số bẩn thành số (int hoặc float).
    Xử lý: khoảng trắng, dấu phẩy ngăn hàng nghìn, dấu ngoặc (số âm), 
    scientific notation, ký tự thừa.
    """
    if val is None or val == "" or val == "-":
        return 0
    
    if isinstance(val, (int, float)):
        return val
    
    s = str(val).strip()
    
    # Xử lý số trong ngoặc → âm: "(224,335)" → -224335
    if s.startswith("(") and s.endswith(")"):
        s = "-" + s[1:-1]
    
    # Loại bỏ khoảng trắng xen giữa số: "1 ,382,335" → "1,382,335"
    s = re.sub(r'\s+', '', s)
    
    # Loại bỏ dấu phẩy ngăn hàng nghìn
    s = s.replace(',', '')
    
    # Loại bỏ dấu ' ở đầu (từ ERP)
    s = s.lstrip("'")
    
    if s == "" or s == "-":
        return 0
    
    try:
        # Thử parse scientific notation trước: "3.26897E+11"
        f = float(s)
        # Nếu là số nguyên (không có phần thập phân thực sự)
        if f == int(f) and abs(f) > 1:
            return int(f)
        return f
    except ValueError:
        return 0


def clean_text(val):
    """Làm sạch chuỗi text: loại bỏ newline, khoảng trắng thừa."""
    if val is None:
        return ""
    s = str(val).strip()
    # Thay newline bằng khoảng trắng
    s = re.sub(r'\n+', ' ', s)
    # Loại bỏ khoảng trắng thừa
    s = re.sub(r'\s+', ' ', s)
    return s


def clean_status(val):
    """Chuẩn hóa trạng thái chứng từ."""
    s = clean_text(val)
    
    # Xử lý các trường hợp bị ngắt dòng
    status_map = {
        "Not Reversed": "Not Reversed",
        "NotReversed": "Not Reversed",
        "RNeovt ersed": "Not Reversed",  # OCR lỗi
        "Reversed Not": "Not Reversed",
        "Reversed": "Reversed",
        "Complete": "Complete",
        "Draft": "Draft",
        "Unpost": "Unpost",
        "Cleared": "Cleared",
        "Posted": "Posted",
    }
    
    for key, value in status_map.items():
        if key.lower() in s.lower():
            return value
    
    return s if s else "Unknown"


def clean_date(val):
    """Parse chuỗi ngày tháng."""
    if val is None or val == "":
        return None
    s = clean_text(val)
    
    # Các format thường gặp
    formats = [
        "%d-%b-%y",     # 30-Apr-26
        "%d-%m-%y",     # 30-04-26
        "%d/%m/%Y",     # 30/04/2026
        "%d-%m-%Y",     # 30-04-2026
        "%d/%m/%y",     # 30/04/26
    ]
    
    for fmt in formats:
        try:
            return pd.to_datetime(s, format=fmt)
        except (ValueError, TypeError):
            continue
    
    return None


def extract_product_code(text):
    """
    Trích xuất mã sản phẩm từ cột Nội dung.
    Ví dụ: "DIEN01-DOANH THU..." → "DIEN01"
    """
    if not text:
        return ""
    s = clean_text(text)
    
    # Pattern: Mã sản phẩm nằm ở đầu, theo sau bởi dấu "-" hoặc khoảng trắng
    patterns = [
        r'^(DIEN\d+)',
        r'^(CSPK\d+)',
        r'^(4500\w+)',
        r'^(1388\w+)',
        r'^(5118\w+)',
    ]
    
    for pattern in patterns:
        match = re.match(pattern, s, re.IGNORECASE)
        if match:
            return match.group(1).upper()
    
    # Tìm trong toàn bộ text
    for pattern in patterns:
        match = re.search(pattern, s, re.IGNORECASE)
        if match:
            return match.group(1).upper()
    
    return ""


def is_data_row(row):
    """Kiểm tra xem một row có phải là dòng dữ liệu (không phải header/summary)."""
    if not row:
        return False
    
    # Dòng toàn None
    if all(v is None or v == "" for v in row):
        return False
    
    first = str(row[0]).strip() if row[0] else ""
    
    # Dòng header thường
    skip_prefixes = ["Tổng", "Cộng", "TỔNG", "CỘNG", "Tài khoản:", "Dư đầu", "Dư cuối"]
    for prefix in skip_prefixes:
        if first.startswith(prefix):
            return False
    
    return True


def safe_sum(series):
    """Tính tổng an toàn cho pandas Series."""
    return pd.to_numeric(series, errors='coerce').fillna(0).sum()
