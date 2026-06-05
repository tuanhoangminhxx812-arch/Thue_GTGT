# -*- coding: utf-8 -*-
"""
Parser cho Báo cáo GCS (Ghi chỉ số - Hóa đơn phát hành).
Đọc file PDF xuất từ ERP EVN, phân tách theo loại hóa đơn.
"""

import pandas as pd
import pdfplumber
from .utils import clean_number, clean_text, clean_date


def parse_gcs(file_or_path):
    """
    Parse file PDF báo cáo GCS.
    
    Returns:
        dict: {
            'summary': DataFrame tổng hợp theo loại HĐ,
            'detail': DataFrame chi tiết từng dòng,
            'totals': dict các số tổng cộng
        }
    """
    if isinstance(file_or_path, str):
        pdf = pdfplumber.open(file_or_path)
    else:
        pdf = pdfplumber.open(file_or_path)
    
    all_rows = []
    current_type = "Không xác định"
    
    for page in pdf.pages:
        tables = page.extract_tables()
        if not tables:
            continue
        
        for table in tables:
            for row in table:
                if not row or len(row) < 10:
                    continue
                
                first_cell = clean_text(row[0]) if row[0] else ""
                
                # Detect loại hóa đơn
                if "Loại hoá đơn" in first_cell or "Loại hóa đơn" in first_cell:
                    if "Hủy bỏ" in first_cell:
                        current_type = "Hủy bỏ"
                    elif "Lặp lại" in first_cell:
                        current_type = "Lặp lại"
                    elif "Phát sinh" in first_cell:
                        current_type = "Phát sinh"
                    elif "Thoái hoàn" in first_cell or "Thoái hoàn" in first_cell:
                        current_type = "Thoái hoàn"
                    elif "Truy thu" in first_cell:
                        current_type = "Truy thu"
                    continue
                
                # Skip headers
                if first_cell in ["Stt", "STT", ""] or "SH" in first_cell:
                    continue
                if first_cell.startswith("Tổng") or first_cell.startswith("TIENDIEN"):
                    # Dòng tổng - check if it's sub-total
                    if first_cell.startswith("Tổng số"):
                        # Parse tổng phụ theo loại
                        try:
                            total_row = {
                                "loai_hoa_don": current_type,
                                "is_subtotal": True,
                                "tien_dien": clean_number(row[8] if len(row) > 8 else 0),
                                "thue_dien": clean_number(row[9] if len(row) > 9 else 0),
                                "tong_tien_dien": clean_number(row[10] if len(row) > 10 else 0),
                                "tien_cspk": clean_number(row[11] if len(row) > 11 else 0),
                                "thue_cspk": clean_number(row[12] if len(row) > 12 else 0),
                                "tong_tien_cspk": clean_number(row[13] if len(row) > 13 else 0),
                                "tong_cong": clean_number(row[14] if len(row) > 14 else 0),
                            }
                            all_rows.append(total_row)
                        except (IndexError, ValueError):
                            pass
                    continue
                
                # Skip null rows
                if all(v is None or v == "" for v in row):
                    continue
                
                # Data row
                try:
                    stt = clean_text(row[0])
                    # Kiểm tra xem STT có phải là số
                    try:
                        int(stt)
                    except (ValueError, TypeError):
                        continue
                    
                    data_row = {
                        "stt": int(stt),
                        "loai_hoa_don": current_type,
                        "is_subtotal": False,
                        "ngay_ghi_so": clean_text(row[1]),
                        "so_gcs": clean_number(row[2]),
                        "so_hoa_don": clean_number(row[3]),
                        "ngay_phat_hanh": clean_text(row[4]),
                        "dien_nang_sh": clean_number(row[5]),
                        "dien_nang_ngoai_sh": clean_number(row[6]),
                        "dien_nang_tong": clean_number(row[7]),
                        "tien_dien": clean_number(row[8]),
                        "thue_dien": clean_number(row[9]),
                        "tong_tien_dien": clean_number(row[10]),
                        "tien_cspk": clean_number(row[11]),
                        "thue_cspk": clean_number(row[12]),
                        "tong_tien_cspk": clean_number(row[13]),
                        "tong_cong": clean_number(row[14]),
                    }
                    all_rows.append(data_row)
                except (IndexError, ValueError):
                    continue
    
    pdf.close()
    
    if not all_rows:
        return {"summary": pd.DataFrame(), "detail": pd.DataFrame(), "data": pd.DataFrame(), "totals": {}}
    
    df = pd.DataFrame(all_rows)
    
    # Tách detail và subtotals
    detail = df[df["is_subtotal"] == False].copy()
    subtotals = df[df["is_subtotal"] == True].copy()
    
    # Tính tổng cộng
    detail_data = detail.copy()
    totals = {
        "tien_dien": detail_data["tien_dien"].sum(),
        "thue_dien": detail_data["thue_dien"].sum(),
        "tong_tien_dien": detail_data["tong_tien_dien"].sum(),
        "tien_cspk": detail_data["tien_cspk"].sum(),
        "thue_cspk": detail_data["thue_cspk"].sum(),
        "tong_tien_cspk": detail_data["tong_tien_cspk"].sum(),
        "tong_cong": detail_data["tong_cong"].sum(),
    }
    
    # Summary theo loại hóa đơn
    summary = detail.groupby("loai_hoa_don").agg({
        "tien_dien": "sum",
        "thue_dien": "sum",
        "tong_tien_dien": "sum",
        "tien_cspk": "sum",
        "thue_cspk": "sum",
        "tong_tien_cspk": "sum",
        "tong_cong": "sum",
        "stt": "count",
    }).rename(columns={"stt": "so_luong"}).reset_index()
    
    return {
        "summary": summary,
        "detail": detail.drop(columns=["is_subtotal"]),
        "data": detail.drop(columns=["is_subtotal"]),
        "totals": totals,
    }
