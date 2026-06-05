# -*- coding: utf-8 -*-
"""
Tax Calculator - Tính toán chỉ tiêu Tờ khai Thuế GTGT (Mẫu 01/GTGT).
Module 4: Trích xuất số liệu lên tờ khai thuế.
"""

import pandas as pd
from config import TAX_RATE_MAP


class TaxCalculator:
    """Tính toán các chỉ tiêu tờ khai thuế GTGT mẫu 01/GTGT."""
    
    def __init__(self, data_store, khau_tru_ky_truoc=0):
        """
        Args:
            data_store: dict chứa tất cả dữ liệu đã parse
            khau_tru_ky_truoc: Thuế GTGT còn khấu trừ kỳ trước (nhập tay)
        """
        self.data = data_store
        self.khau_tru_ky_truoc = khau_tru_ky_truoc
    
    def calculate(self):
        """
        Tính toán tất cả chỉ tiêu tờ khai.
        
        Returns:
            dict: key = số chỉ tiêu, value = giá trị
        """
        result = {}
        
        # ============================================================
        # PHẦN MUA VÀO (Chỉ tiêu 22-25)
        # ============================================================
        
        # [22] Thuế GTGT còn được khấu trừ kỳ trước chuyển sang
        result[22] = self.khau_tru_ky_truoc
        
        # Lấy dữ liệu TA036 (mua vào)
        ta036 = self.data.get("ta036", {})
        ta036_totals = ta036.get("totals", {}) if ta036 else {}
        
        # [23] Giá trị HHDV mua vào
        result[23] = ta036_totals.get("tong_doanh_so", 0)
        
        # [24] Thuế GTGT mua vào được khấu trừ
        result[24] = ta036_totals.get("tong_thue_gtgt", 0)
        
        # [25] Tổng thuế GTGT được khấu trừ = [22] + [24]
        result[25] = result[22] + result[24]
        
        # ============================================================
        # PHẦN BÁN RA (Chỉ tiêu 26-35)
        # ============================================================
        
        # Lấy dữ liệu TA035 (bán ra)
        ta035 = self.data.get("ta035", {}).get("data", pd.DataFrame())
        
        # Phân loại theo thuế suất
        sales_0 = {"doanh_so": 0, "thue": 0}
        sales_5 = {"doanh_so": 0, "thue": 0}
        sales_8 = {"doanh_so": 0, "thue": 0}
        sales_10 = {"doanh_so": 0, "thue": 0}
        sales_not_taxed = {"doanh_so": 0, "thue": 0}
        
        if not ta035.empty:
            for _, row in ta035.iterrows():
                thue_suat = int(row.get("thue_suat", 0))
                doanh_so = row.get("doanh_so", 0)
                thue = row.get("thue_gtgt", 0)
                nhom = row.get("nhom_thue", "")
                
                if "Không chịu thuế" in nhom:
                    sales_not_taxed["doanh_so"] += doanh_so
                    sales_not_taxed["thue"] += thue
                elif thue_suat == 0:
                    sales_0["doanh_so"] += doanh_so
                    sales_0["thue"] += thue
                elif thue_suat == 5:
                    sales_5["doanh_so"] += doanh_so
                    sales_5["thue"] += thue
                elif thue_suat == 8:
                    sales_8["doanh_so"] += doanh_so
                    sales_8["thue"] += thue
                elif thue_suat == 10:
                    sales_10["doanh_so"] += doanh_so
                    sales_10["thue"] += thue
        
        # [26] HHDV bán ra không chịu thuế GTGT
        result[26] = sales_not_taxed["doanh_so"]
        
        # [27] HHDV bán ra chịu thuế 0%
        result[27] = sales_0["doanh_so"]
        
        # [29] HHDV bán ra chịu thuế 5%
        result[29] = sales_5["doanh_so"]
        
        # [30] Thuế GTGT 5%
        result[30] = sales_5["thue"]
        
        # [32] HHDV bán ra chịu thuế 8%
        result[32] = sales_8["doanh_so"]
        
        # [33] Thuế GTGT 8%
        result[33] = sales_8["thue"]
        
        # [32a] HHDV bán ra chịu thuế 10%
        result["32a"] = sales_10["doanh_so"]
        
        # [33a] Thuế GTGT 10%
        result["33a"] = sales_10["thue"]
        
        # [34] Tổng doanh số HHDV bán ra
        result[34] = result[26] + result[27] + result[29] + result[32] + result.get("32a", 0)
        
        # [35] Tổng thuế GTGT HHDV bán ra
        result[35] = result[30] + result[33] + result.get("33a", 0)
        
        # ============================================================
        # TÍNH TOÁN CUỐI CÙNG (Chỉ tiêu 36-42)
        # ============================================================
        
        # [36] Thuế GTGT phát sinh trong kỳ = [35] - [25]
        result[36] = result[35] - result[25]
        
        # [37] Thuế GTGT phải nộp trong kỳ
        if result[36] >= 0:
            result[37] = result[36]
            result[38] = 0
        else:
            result[37] = 0
            result[38] = abs(result[36])  # [38] Chưa khấu trừ hết
        
        # [40] Thuế GTGT đề nghị hoàn (thường = 0 trừ khi có đề nghị)
        result[40] = 0
        
        # [41] Thuế GTGT còn được khấu trừ chuyển kỳ sau = [38] - [40]
        result[41] = result[38] - result[40]
        
        # [42] Tổng doanh thu (tham khảo)
        result[42] = result[34]
        
        return result
    
    def get_declaration_table(self):
        """
        Tạo bảng tổng hợp chỉ tiêu tờ khai theo format chuẩn.
        
        Returns:
            DataFrame với columns: [Chi tiêu, Mã số, Giá trị]
        """
        values = self.calculate()
        
        rows = [
            {"nhom": "A. THUẾ GTGT ĐƯỢC KHẤU TRỪ", "chi_tieu": "", "ma_so": "", "gia_tri": ""},
            {"nhom": "", "chi_tieu": "Thuế GTGT còn được khấu trừ kỳ trước chuyển sang", "ma_so": "[22]", "gia_tri": values.get(22, 0)},
            {"nhom": "", "chi_tieu": "Giá trị hàng hóa, dịch vụ mua vào", "ma_so": "[23]", "gia_tri": values.get(23, 0)},
            {"nhom": "", "chi_tieu": "Thuế GTGT của HHDV mua vào", "ma_so": "[24]", "gia_tri": values.get(24, 0)},
            {"nhom": "", "chi_tieu": "Tổng số thuế GTGT được khấu trừ kỳ này ([25]=[22]+[24])", "ma_so": "[25]", "gia_tri": values.get(25, 0)},
            
            {"nhom": "B. HÀNG HÓA, DỊCH VỤ BÁN RA", "chi_tieu": "", "ma_so": "", "gia_tri": ""},
            {"nhom": "", "chi_tieu": "HHDV bán ra không chịu thuế GTGT", "ma_so": "[26]", "gia_tri": values.get(26, 0)},
            {"nhom": "", "chi_tieu": "HHDV bán ra chịu thuế suất 0%", "ma_so": "[27]", "gia_tri": values.get(27, 0)},
            {"nhom": "", "chi_tieu": "HHDV bán ra chịu thuế suất 5%", "ma_so": "[29]", "gia_tri": values.get(29, 0)},
            {"nhom": "", "chi_tieu": "Thuế GTGT của HHDV chịu thuế 5%", "ma_so": "[30]", "gia_tri": values.get(30, 0)},
            {"nhom": "", "chi_tieu": "HHDV bán ra chịu thuế suất 8%", "ma_so": "[32]", "gia_tri": values.get(32, 0)},
            {"nhom": "", "chi_tieu": "Thuế GTGT của HHDV chịu thuế 8%", "ma_so": "[33]", "gia_tri": values.get(33, 0)},
            {"nhom": "", "chi_tieu": "HHDV bán ra chịu thuế suất 10%", "ma_so": "[32a]", "gia_tri": values.get("32a", 0)},
            {"nhom": "", "chi_tieu": "Thuế GTGT của HHDV chịu thuế 10%", "ma_so": "[33a]", "gia_tri": values.get("33a", 0)},
            {"nhom": "", "chi_tieu": "Tổng doanh số HHDV bán ra ([34]=[26]+[27]+[29]+[32]+[32a])", "ma_so": "[34]", "gia_tri": values.get(34, 0)},
            {"nhom": "", "chi_tieu": "Tổng thuế GTGT HHDV bán ra ([35]=[30]+[33]+[33a])", "ma_so": "[35]", "gia_tri": values.get(35, 0)},
            
            {"nhom": "C. XÁC ĐỊNH THUẾ GTGT PHẢI NỘP", "chi_tieu": "", "ma_so": "", "gia_tri": ""},
            {"nhom": "", "chi_tieu": "Thuế GTGT phát sinh trong kỳ ([36]=[35]-[25])", "ma_so": "[36]", "gia_tri": values.get(36, 0)},
            {"nhom": "", "chi_tieu": "Thuế GTGT phải nộp trong kỳ", "ma_so": "[37]", "gia_tri": values.get(37, 0)},
            {"nhom": "", "chi_tieu": "Thuế GTGT chưa khấu trừ hết kỳ này", "ma_so": "[38]", "gia_tri": values.get(38, 0)},
            {"nhom": "", "chi_tieu": "Thuế GTGT đề nghị hoàn", "ma_so": "[40]", "gia_tri": values.get(40, 0)},
            {"nhom": "", "chi_tieu": "Thuế GTGT còn được khấu trừ chuyển kỳ sau ([41]=[38]-[40])", "ma_so": "[41]", "gia_tri": values.get(41, 0)},
        ]
        
        return pd.DataFrame(rows)
