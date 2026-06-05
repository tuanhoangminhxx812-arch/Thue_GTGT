# -*- coding: utf-8 -*-
"""
Parser cho Sổ cái TA030 (TK3331 - Thuế đầu ra, TK1331 - Thuế đầu vào).
"""

import pandas as pd
import pdfplumber
from .utils import clean_number, clean_text, clean_status, extract_product_code


def parse_ta030(file_or_path, account_type="output"):
    """
    Parse file PDF Sổ cái TA030 (TK3331 hoặc TK1331).
    
    Args:
        file_or_path: đường dẫn file hoặc file object
        account_type: "output" (TK3331 - thuế đầu ra) hoặc "input" (TK1331 - thuế đầu vào)
    
    Returns:
        dict: {
            'data': DataFrame chi tiết giao dịch,
            'by_account': DataFrame theo sub-account,
            'totals': dict tổng cộng,
            'opening_balance': số dư đầu kỳ,
            'closing_balance': số dư cuối kỳ
        }
    """
    if isinstance(file_or_path, str):
        pdf = pdfplumber.open(file_or_path)
    else:
        pdf = pdfplumber.open(file_or_path)
    
    all_rows = []
    current_account = ""
    opening_balance = 0
    closing_balance = 0
    total_opening = 0
    total_debit = 0
    total_credit = 0
    
    for page in pdf.pages:
        tables = page.extract_tables()
        if not tables:
            continue
        
        for table in tables:
            for row in table:
                if not row or len(row) < 6:
                    continue
                
                first_cell = clean_text(row[0]) if row[0] else ""
                
                # Detect sub-account
                if "Tài khoản:" in first_cell:
                    import re
                    match = re.search(r'(\d{11,})', first_cell)
                    if match:
                        current_account = match.group(1)
                    # Check dư đầu kỳ
                    dien_giai = clean_text(row[3]) if len(row) > 3 else ""
                    if "Dư đầu kỳ" in dien_giai:
                        col_no = clean_number(row[4]) if len(row) > 4 else 0
                        col_co = clean_number(row[5]) if len(row) > 5 else 0
                        opening_balance += (col_no if col_no != 0 else col_co)
                    continue
                
                # Skip headers
                if first_cell in ["CHỨNG TỪ", "Ngày chứng từ", ""]:
                    continue
                
                # Dòng tổng
                dien_giai = clean_text(row[3]) if len(row) > 3 else ""
                if "Tổng Dư đầu kỳ" in dien_giai:
                    total_opening = clean_number(row[4]) if len(row) > 4 else 0
                    continue
                if "Tổng Cộng phát sinh" in dien_giai:
                    total_debit = clean_number(row[4]) if len(row) > 4 else 0
                    total_credit = clean_number(row[5]) if len(row) > 5 else 0
                    continue
                if "Tổng Dư cuối kỳ" in dien_giai:
                    closing_balance = clean_number(row[4]) if len(row) > 4 else 0
                    if closing_balance == 0:
                        closing_balance = clean_number(row[5]) if len(row) > 5 else 0
                    continue
                if "Cộng phát sinh" in dien_giai or "Dư cuối kỳ" in dien_giai or "Dư đầu kỳ" in dien_giai:
                    continue
                
                # Parse date to determine if it's a data row
                ngay_ct = clean_text(row[0])
                if not ngay_ct or len(ngay_ct) < 6:
                    continue
                
                # Kiểm tra format ngày: dd-mm-yy hoặc dd-Mmm-yy
                import re as re2
                if not re2.match(r'\d{2}-\w{2,3}-\d{2}', ngay_ct):
                    continue
                
                try:
                    product_code = extract_product_code(dien_giai)
                    
                    data_row = {
                        "sub_account": current_account,
                        "ngay_ct": ngay_ct,
                        "so_ct": clean_text(row[1]),
                        "nguon_ct": clean_text(row[2]),
                        "dien_giai": dien_giai,
                        "phat_sinh_no": clean_number(row[4]) if len(row) > 4 else 0,
                        "phat_sinh_co": clean_number(row[5]) if len(row) > 5 else 0,
                        "nguoi_hach_toan": clean_text(row[6]) if len(row) > 6 else "",
                        "trang_thai": clean_status(row[7]) if len(row) > 7 else "",
                        "ma_san_pham": product_code,
                    }
                    all_rows.append(data_row)
                except (IndexError, ValueError):
                    continue
    
    pdf.close()
    
    if not all_rows:
        return {
            "data": pd.DataFrame(),
            "by_account": pd.DataFrame(),
            "totals": {"tong_no": 0, "tong_co": 0},
            "opening_balance": total_opening if total_opening else opening_balance,
            "closing_balance": closing_balance,
        }
    
    df = pd.DataFrame(all_rows)
    
    # Tổng hợp theo sub-account
    by_account = df.groupby("sub_account").agg({
        "phat_sinh_no": "sum",
        "phat_sinh_co": "sum",
        "so_ct": "count",
    }).rename(columns={"so_ct": "so_giao_dich"}).reset_index()
    
    totals = {
        "tong_no": total_debit if total_debit else df["phat_sinh_no"].sum(),
        "tong_co": total_credit if total_credit else df["phat_sinh_co"].sum(),
    }
    
    return {
        "data": df,
        "by_account": by_account,
        "totals": totals,
        "opening_balance": total_opening if total_opening else opening_balance,
        "closing_balance": closing_balance,
    }
