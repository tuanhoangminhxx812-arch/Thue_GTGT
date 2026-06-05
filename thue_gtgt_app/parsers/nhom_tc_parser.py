# -*- coding: utf-8 -*-
"""
Parser cho báo cáo chi tiết khách hàng Nhôm Toàn Cầu.
"""

import pandas as pd
import pdfplumber
from .utils import clean_number, clean_text


def parse_nhom_tc(file_or_path):
    """
    Parse file PDF chi tiết khách hàng Nhôm Toàn Cầu.
    
    Returns:
        dict: {
            'data': DataFrame chi tiết,
            'totals': dict tổng cộng,
            'trong_thang': tổng trong tháng,
            'cuoi_thang': tổng cuối tháng
        }
    """
    if isinstance(file_or_path, str):
        pdf = pdfplumber.open(file_or_path)
    else:
        pdf = pdfplumber.open(file_or_path)
    
    all_rows = []
    trong_thang = 0
    cuoi_thang = 0
    tong_cong = 0
    
    for page in pdf.pages:
        tables = page.extract_tables()
        if not tables:
            continue
        
        for table in tables:
            for row in table:
                if not row or len(row) < 8:
                    continue
                
                # Tìm dòng TRONGTHANG / CUOITHANG
                for i, cell in enumerate(row):
                    cell_text = clean_text(cell)
                    if "TRONGTHANG" in cell_text:
                        # Giá trị ở cột kế bên hoặc cột cuối
                        for j in range(len(row)-1, i, -1):
                            val = clean_number(row[j])
                            if val != 0:
                                trong_thang = val
                                break
                    elif "CUOITHANG" in cell_text:
                        for j in range(len(row)-1, i, -1):
                            val = clean_number(row[j])
                            if val != 0:
                                cuoi_thang = val
                                break
                
                first_cell = clean_text(row[0]) if row[0] else ""
                
                # Skip headers
                if first_cell in ["STT", ""] or "Mã Khách Hàng" in clean_text(row[1] if len(row) > 1 else ""):
                    continue
                
                # Parse data row
                try:
                    stt = int(first_cell)
                except (ValueError, TypeError):
                    continue
                
                try:
                    data_row = {
                        "stt": stt,
                        "ma_khach_hang": clean_text(row[1]) if len(row) > 1 else "",
                        "danh_so": clean_text(row[2]) if len(row) > 2 else "",
                        "dia_chi": clean_text(row[3]) if len(row) > 3 else "",
                        "ky_thang": clean_text(row[4]) if len(row) > 4 else "",
                        "ngay_phat_hanh": clean_text(row[5]) if len(row) > 5 else "",
                        "loai_hd": clean_text(row[6]) if len(row) > 6 else "",
                        "dien_tieu_thu": clean_number(row[7]) if len(row) > 7 else 0,
                        "tien_ps": clean_number(row[8]) if len(row) > 8 else 0,
                        "thue_ps": clean_number(row[9]) if len(row) > 9 else 0,
                        "tong_tien": clean_number(row[10]) if len(row) > 10 else 0,
                    }
                    if data_row["tien_ps"] != 0 or data_row["tong_tien"] != 0:
                        all_rows.append(data_row)
                except (IndexError, ValueError):
                    continue
    
    pdf.close()
    
    if not all_rows:
        df = pd.DataFrame()
    else:
        df = pd.DataFrame(all_rows)
    
    tong_cong = trong_thang + cuoi_thang
    
    totals = {
        "trong_thang": trong_thang,
        "cuoi_thang": cuoi_thang,
        "tong_cong": tong_cong,
        "tong_tien_ps": df["tien_ps"].sum() if not df.empty else 0,
    }
    
    return {
        "data": df,
        "totals": totals,
        "trong_thang": trong_thang,
        "cuoi_thang": cuoi_thang,
    }
