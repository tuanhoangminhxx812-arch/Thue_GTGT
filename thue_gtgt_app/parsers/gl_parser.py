# -*- coding: utf-8 -*-
"""
Parser cho Sổ cái TK511 (GL_0903).
Đọc báo cáo liệt kê giao dịch phát sinh theo tài khoản doanh thu.
"""

import pandas as pd
import pdfplumber
from .utils import clean_number, clean_text, clean_status, extract_product_code


def parse_gl_tk511(file_or_path):
    """
    Parse file PDF Sổ cái TK511.
    
    Returns:
        dict: {
            'data': DataFrame chi tiết giao dịch,
            'by_product': DataFrame tổng hợp theo mã sản phẩm,
            'totals': dict tổng cộng
        }
    """
    if isinstance(file_or_path, str):
        pdf = pdfplumber.open(file_or_path)
    else:
        pdf = pdfplumber.open(file_or_path)
    
    all_rows = []
    
    for page in pdf.pages:
        tables = page.extract_tables()
        if not tables:
            continue
        
        for table in tables:
            for row in table:
                if not row or len(row) < 15:
                    continue
                
                first_cell = clean_text(row[0]) if row[0] else ""
                
                # Skip headers, title rows
                if first_cell in ["", "phát sinh", "HCMC"] or "Báo cáo" in first_cell:
                    continue
                if first_cell in ["Nguồn", "nguon_ps"]:
                    continue
                
                # Chỉ lấy dòng có nguồn phát sinh hợp lệ
                if first_cell not in ["AR_TRANS", "GL", "AR_REC", "AP_TRANS"]:
                    continue
                
                try:
                    noi_dung = clean_text(row[17] if len(row) > 17 else "")
                    product_code = extract_product_code(noi_dung)
                    
                    data_row = {
                        "nguon_ps": first_cell,
                        "so_gd": clean_text(row[1]),
                        "ngay_gd": clean_text(row[2]),
                        "tai_khoan": clean_text(row[5]) if len(row) > 5 else "",
                        "loai_hinh": clean_text(row[6]) if len(row) > 6 else "",
                        "san_pham": clean_text(row[7]) if len(row) > 7 else "",
                        "no_nguyen_te": clean_number(row[13] if len(row) > 13 else 0),
                        "co_nguyen_te": clean_number(row[14] if len(row) > 14 else 0),
                        "no_quy_doi": clean_number(row[15] if len(row) > 15 else 0),
                        "co_quy_doi": clean_number(row[16] if len(row) > 16 else 0),
                        "noi_dung": noi_dung,
                        "ma_san_pham": product_code,
                        "trang_thai": clean_status(row[18] if len(row) > 18 else ""),
                    }
                    all_rows.append(data_row)
                except (IndexError, ValueError):
                    continue
    
    pdf.close()
    
    if not all_rows:
        return {"data": pd.DataFrame(), "by_product": pd.DataFrame(), "totals": {}}
    
    df = pd.DataFrame(all_rows)
    
    # Tổng hợp theo mã sản phẩm
    by_product = df.groupby("ma_san_pham").agg({
        "co_quy_doi": "sum",
        "no_quy_doi": "sum",
        "so_gd": "count",
    }).rename(columns={
        "co_quy_doi": "tong_co",
        "no_quy_doi": "tong_no",
        "so_gd": "so_giao_dich",
    }).reset_index()
    
    # Tổng cộng
    totals = {
        "tong_co": df["co_quy_doi"].sum(),
        "tong_no": df["no_quy_doi"].sum(),
    }
    
    return {
        "data": df,
        "by_product": by_product,
        "totals": totals,
    }
