# -*- coding: utf-8 -*-
"""
Parser cho Bảng kê TA036 (Mua vào - TK13311).
"""

import pandas as pd
import pdfplumber
from .utils import clean_number, clean_text, clean_status


def parse_ta036(file_or_path):
    """
    Parse file PDF Bảng kê TA036 (mua vào).
    
    Returns:
        dict: {
            'data': DataFrame chi tiết,
            'by_category': DataFrame tổng hợp theo nhóm,
            'totals': dict tổng cộng (chỉ nhóm đủ ĐK khấu trừ)
        }
    """
    if isinstance(file_or_path, str):
        pdf = pdfplumber.open(file_or_path)
    else:
        pdf = pdfplumber.open(file_or_path)
    
    all_rows = []
    current_group = ""
    group_map = {
        "1": "Dùng riêng cho SXKD chịu thuế đủ ĐK khấu trừ",
        "2": "Không đủ điều kiện khấu trừ",
        "3": "Dùng chung đủ ĐK khấu trừ",
        "4": "Dự án đầu tư đủ ĐK khấu trừ",
        "5": "Không tổng hợp trên tờ khai",
        "6": "Có số liệu nhưng không lên bảng kê",
    }
    
    for page in pdf.pages:
        tables = page.extract_tables()
        if not tables:
            continue
        
        for table in tables:
            for row in table:
                if not row or len(row) < 10:
                    continue
                
                first_cell = clean_text(row[0]) if row[0] else ""
                full_text = clean_text(" ".join([str(c) for c in row if c]))
                
                # Detect nhóm
                for key, value in group_map.items():
                    pattern = f"{key}."
                    if (first_cell.startswith(pattern) or first_cell == f"{key}. Hàng") and (
                        "Hàng hóa" in full_text or "hàng hóa" in full_text or 
                        "Có số liệu" in full_text or "Không đủ" in full_text or
                        "Dùng" in full_text or "Dự án" in full_text):
                        current_group = value
                        break
                
                # Skip headers
                if first_cell in ["STT", "[1]", ""] or (row[1] and clean_text(row[1]) in ["[2]", "Ký hiệu"]):
                    continue
                
                # Dòng tổng
                if "Tổng" in first_cell or "cộng" in first_cell.lower():
                    continue
                
                # Check STT hợp lệ
                stt_val = first_cell.strip()
                try:
                    stt_num = int(stt_val)
                except (ValueError, TypeError):
                    continue
                
                try:
                    doanh_so = clean_number(row[7]) if len(row) > 7 else 0
                    thue_suat = clean_number(row[8]) if len(row) > 8 else 0
                    thue_gtgt = clean_number(row[9]) if len(row) > 9 else 0
                    mat_hang = clean_text(row[6]) if len(row) > 6 else ""
                    trang_thai = clean_status(row[18]) if len(row) > 18 else ""
                    
                    # Skip mẫu trống
                    if doanh_so == 0 and thue_gtgt == 0 and not mat_hang:
                        continue
                    
                    data_row = {
                        "stt": stt_num,
                        "nhom": current_group,
                        "ky_hieu_hd": clean_text(row[1]) if len(row) > 1 else "",
                        "so_hoa_don": clean_text(row[2]) if len(row) > 2 else "",
                        "ngay_phat_hanh": clean_text(row[3]) if len(row) > 3 else "",
                        "ten_nguoi_ban": clean_text(row[4]) if len(row) > 4 else "",
                        "ma_so_thue": clean_text(row[5]) if len(row) > 5 else "",
                        "mat_hang": mat_hang,
                        "doanh_so": doanh_so,
                        "thue_suat": thue_suat,
                        "thue_gtgt": thue_gtgt,
                        "ghi_chu": clean_text(row[10]) if len(row) > 10 else "",
                        "nguon_ct": clean_text(row[11]) if len(row) > 11 else "",
                        "so_ct": clean_text(row[12]) if len(row) > 12 else "",
                        "ngay_lap_ct": clean_text(row[13]) if len(row) > 13 else "",
                        "so_tien_da_tt": clean_number(row[15]) if len(row) > 15 else 0,
                        "nguoi_lap_ct": clean_text(row[17]) if len(row) > 17 else "",
                        "trang_thai": trang_thai,
                    }
                    all_rows.append(data_row)
                except (IndexError, ValueError):
                    continue
    
    pdf.close()
    
    if not all_rows:
        return {
            "data": pd.DataFrame(),
            "by_category": pd.DataFrame(),
            "totals": {"tong_doanh_so": 0, "tong_thue_gtgt": 0},
        }
    
    df = pd.DataFrame(all_rows)
    
    # Tổng hợp theo nhóm
    by_category = df.groupby("nhom").agg({
        "doanh_so": "sum",
        "thue_gtgt": "sum",
        "stt": "count",
    }).rename(columns={"stt": "so_luong"}).reset_index()
    
    # Tổng chỉ lấy nhóm đủ điều kiện khấu trừ
    deductible_groups = [
        "Dùng riêng cho SXKD chịu thuế đủ ĐK khấu trừ",
        "Dùng chung đủ ĐK khấu trừ",
        "Dự án đầu tư đủ ĐK khấu trừ",
    ]
    df_deductible = df[df["nhom"].isin(deductible_groups)]
    
    totals = {
        "tong_doanh_so": df_deductible["doanh_so"].sum(),
        "tong_thue_gtgt": df_deductible["thue_gtgt"].sum(),
        "tong_doanh_so_all": df["doanh_so"].sum(),
        "tong_thue_gtgt_all": df["thue_gtgt"].sum(),
    }
    
    return {
        "data": df,
        "by_category": by_category,
        "totals": totals,
    }
