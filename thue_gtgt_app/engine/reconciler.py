# -*- coding: utf-8 -*-
"""
Reconciliation Engine - Tạo bảng đối chiếu tổng hợp theo mẫu TAX_VTA.
Module 3: Dashboard đối chiếu tự động.
"""

import pandas as pd
import numpy as np
from config import TAX_RATE_MAP, PRODUCT_NAME_MAP, PRODUCT_DISPLAY_ORDER


class ReconciliationEngine:
    """Động cơ đối chiếu tự động tạo báo cáo dạng TAX_VTA."""
    
    def __init__(self, data_store):
        self.data = data_store
    
    def build_summary_table(self):
        """
        Tạo bảng tổng hợp Doanh số và Tiền thuế theo mã sản phẩm.
        Tương tự Table 5 trong TAX_VTA.
        
        Columns: Mã, TA035_DS, TA035_Thue, GCS_T_truoc_DS, GCS_T_truoc_Thue,
                 GCS_T_hien_tai_DS, GCS_T_hien_tai_Thue, CLech_DS, CLech_Thue
        """
        ta035 = self.data.get("ta035", {}).get("data", pd.DataFrame())
        
        if ta035.empty:
            return pd.DataFrame()
        
        # Tổng hợp TA035 theo mã hàng
        ta035_summary = ta035.groupby("mat_hang").agg({
            "doanh_so": "sum",
            "thue_gtgt": "sum",
        }).reset_index()
        ta035_summary.columns = ["ma", "ta035_doanh_so", "ta035_thue"]
        
        # Dữ liệu GCS
        gcs = self.data.get("gcs", {})
        gcs_totals = gcs.get("totals", {}) if gcs else {}
        
        # GCS chỉ có tiền điện (DIEN01 + DIEN00) và CSPK (CSPK02 + CSPK00)
        # Các mã khác (4500TT, 1388DD) không nằm trong GCS
        gcs_rows = []
        if gcs_totals:
            gcs_tien_dien = gcs_totals.get("tien_dien", 0)
            gcs_thue_dien = gcs_totals.get("thue_dien", 0)
            gcs_tien_cspk = gcs_totals.get("tien_cspk", 0)
            gcs_thue_cspk = gcs_totals.get("thue_cspk", 0)
            
            # Phân tách GCS cho DIEN00 từ Nhôm Toàn Cầu
            nhom_tc = self.data.get("nhom_tc", {})
            nhom_tc_totals = nhom_tc.get("totals", {}) if nhom_tc else {}
            nhom_tc_tien = nhom_tc_totals.get("tong_cong", 0) if nhom_tc_totals else 0
            
            # DIEN00 = tiền Nhôm Toàn Cầu, DIEN01 = tổng - DIEN00
            gcs_rows.append({"ma": "DIEN00", "gcs_doanh_so": nhom_tc_tien, "gcs_thue": 0})
            gcs_rows.append({"ma": "DIEN01", "gcs_doanh_so": gcs_tien_dien - nhom_tc_tien, "gcs_thue": gcs_thue_dien})
            gcs_rows.append({"ma": "CSPK02", "gcs_doanh_so": gcs_tien_cspk, "gcs_thue": gcs_thue_cspk})
        
        gcs_df = pd.DataFrame(gcs_rows) if gcs_rows else pd.DataFrame(columns=["ma", "gcs_doanh_so", "gcs_thue"])
        
        # Merge
        result = ta035_summary.merge(gcs_df, on="ma", how="outer").fillna(0)
        
        # Tính chênh lệch
        result["clech_doanh_so"] = result["ta035_doanh_so"] - result["gcs_doanh_so"]
        result["clech_thue"] = result["ta035_thue"] - result["gcs_thue"]
        
        # Tính tổng cộng
        total_row = pd.DataFrame([{
            "ma": "Cộng",
            "ta035_doanh_so": result["ta035_doanh_so"].sum(),
            "ta035_thue": result["ta035_thue"].sum(),
            "gcs_doanh_so": result["gcs_doanh_so"].sum(),
            "gcs_thue": result["gcs_thue"].sum(),
            "clech_doanh_so": result["clech_doanh_so"].sum(),
            "clech_thue": result["clech_thue"].sum(),
        }])
        
        result = pd.concat([result, total_row], ignore_index=True)
        
        return result
    
    def build_tax_output_table(self):
        """
        Tạo bảng Thuế đầu ra lên tờ khai.
        Tương tự Table 7 trong TAX_VTA.
        """
        ta035 = self.data.get("ta035", {}).get("data", pd.DataFrame())
        
        if ta035.empty:
            return pd.DataFrame()
        
        rows = []
        
        # Tổng hợp theo mã hàng + thuế suất
        grouped = ta035.groupby(["mat_hang", "thue_suat"]).agg({
            "doanh_so": "sum",
            "thue_gtgt": "sum",
        }).reset_index()
        
        for _, row in grouped.iterrows():
            mat_hang = row["mat_hang"]
            thue_suat = int(row["thue_suat"])
            doanh_so = row["doanh_so"]
            thue_gtgt = row["thue_gtgt"]
            
            ten_loai = PRODUCT_NAME_MAP.get(mat_hang, mat_hang)
            
            rows.append({
                "loai": ten_loai,
                "ma": mat_hang,
                "doanh_so": doanh_so,
                "thue_suat": thue_suat,
                "tien_thue": thue_gtgt,
                "sau_thue": doanh_so + thue_gtgt,
            })
        
        if not rows:
            return pd.DataFrame()
        
        df = pd.DataFrame(rows)
        
        # Tổng cộng
        total_row = pd.DataFrame([{
            "loai": "",
            "ma": "Tổng cộng",
            "doanh_so": df["doanh_so"].sum(),
            "thue_suat": "",
            "tien_thue": df["tien_thue"].sum(),
            "sau_thue": df["sau_thue"].sum(),
        }])
        
        df = pd.concat([df, total_row], ignore_index=True)
        
        return df
    
    def build_cross_check_results(self):
        """
        Tạo kết quả đối chiếu chéo 3 cặp:
        1. KDGCS vs GL33895
        2. TA30 (TK333111) vs TA35
        3. TA36 vs TA30 (TK13311)
        """
        results = []
        
        # 1. GCS vs GL (TK511)
        gcs = self.data.get("gcs", {})
        gl = self.data.get("gl_tk511", {})
        
        gcs_total = gcs.get("totals", {}).get("tong_cong", 0) if gcs else 0
        gl_total = gl.get("totals", {}).get("tong_co", 0) if gl else 0
        
        results.append({
            "name": "KDGCS vs Sổ cái GL (TK511)",
            "source_1": "Báo cáo GCS",
            "value_1": gcs_total,
            "source_2": "Sổ cái TK511",
            "value_2": gl_total,
            "difference": gcs_total - gl_total,
            "note": "So sánh tổng doanh thu + thuế GCS với tổng PS Có TK511",
        })
        
        # 2. TA30 (TK3331) vs TA35
        ta030_3331 = self.data.get("ta030_tk3331", {})
        ta035 = self.data.get("ta035", {})
        
        ta030_co = ta030_3331.get("totals", {}).get("tong_co", 0) if ta030_3331 else 0
        ta035_thue = ta035.get("totals", {}).get("tong_thue_gtgt", 0) if ta035 else 0
        
        results.append({
            "name": "Sổ cái TA30 (TK333111) vs Bảng kê TA35",
            "source_1": "TK3331 (PS Có)",
            "value_1": ta030_co,
            "source_2": "TA035 (Thuế GTGT)",
            "value_2": ta035_thue,
            "difference": ta030_co - ta035_thue,
            "note": "So sánh thuế đầu ra trên sổ cái vs bảng kê",
        })
        
        # 3. TA36 vs TA30 (TK1331)
        ta036 = self.data.get("ta036", {})
        ta030_1331 = self.data.get("ta030_tk1331", {})
        
        ta036_thue = ta036.get("totals", {}).get("tong_thue_gtgt", 0) if ta036 else 0
        ta030_no = ta030_1331.get("totals", {}).get("tong_no", 0) if ta030_1331 else 0
        opening = ta030_1331.get("opening_balance", 0) if ta030_1331 else 0
        ta030_ps_no = ta030_no - opening if ta030_no > opening else ta030_no
        
        results.append({
            "name": "Bảng kê TA36 vs Sổ cái TA30 (TK13311)",
            "source_1": "TA036 (Thuế GTGT mua vào)",
            "value_1": ta036_thue,
            "source_2": "TK1331 (PS Nợ trừ dư ĐK)",
            "value_2": ta030_ps_no,
            "difference": ta036_thue - ta030_ps_no,
            "note": "So sánh thuế đầu vào trên bảng kê vs sổ cái",
        })
        
        return results
    
    def analyze_difference(self, diff_name, diff_value):
        """
        Phân tích nguyên nhân chênh lệch và gợi ý giải pháp.
        
        Returns:
            dict: {cause, suggestion, affected_docs}
        """
        analysis = {
            "cause": "",
            "suggestion": "",
            "affected_docs": pd.DataFrame(),
        }
        
        if diff_value == 0:
            analysis["cause"] = "Không có chênh lệch"
            return analysis
        
        if "TK333111" in diff_name or "TK3331" in diff_name:
            # Tìm chứng từ Unpost/Draft trong TK3331
            ta030_data = self.data.get("ta030_tk3331", {}).get("data", pd.DataFrame())
            if not ta030_data.empty:
                problem_docs = ta030_data[ta030_data["trang_thai"].isin(["Unpost", "Draft", "Not Reversed"])]
                if not problem_docs.empty:
                    analysis["cause"] = (
                        f"Lệch do có {len(problem_docs)} chứng từ chưa ghi sổ (Unpost/Draft) "
                        f"trong Sổ cái TK3331. Tổng giá trị ảnh hưởng: "
                        f"{problem_docs['phat_sinh_co'].sum():,.0f} VND"
                    )
                    analysis["suggestion"] = (
                        "1. Kiểm tra và Post các chứng từ Draft\n"
                        "2. Xác nhận các bút toán Unpost có cần ghi sổ lại không\n"
                        "3. Với chứng từ Not Reversed: kiểm tra đã reverse thành công chưa"
                    )
                    analysis["affected_docs"] = problem_docs
        
        elif "TK13311" in diff_name or "TK1331" in diff_name:
            ta030_data = self.data.get("ta030_tk1331", {}).get("data", pd.DataFrame())
            if not ta030_data.empty:
                problem_docs = ta030_data[ta030_data["trang_thai"].isin(["Unpost", "Not Reversed"])]
                if not problem_docs.empty:
                    analysis["cause"] = (
                        f"Lệch do có {len(problem_docs)} chứng từ chưa được xử lý "
                        f"trong Sổ cái TK1331. Có thể do kết chuyển VAT TK13313 qua TK33311."
                    )
                    analysis["suggestion"] = (
                        "1. Kiểm tra bút toán kết chuyển VAT TK13313 → TK33311 (XDCB)\n"
                        "2. Xác nhận các chứng từ Not Reversed\n"
                        "3. So sánh PS Nợ TK1331 trừ đi dư đầu kỳ"
                    )
                    analysis["affected_docs"] = problem_docs
        
        elif "GCS" in diff_name:
            analysis["cause"] = (
                "Chênh lệch giữa GCS và sổ cái có thể do:\n"
                "- Giao dịch 4500TT (cho thuê trụ điện) hoặc 1388DD (điều động VTTB) "
                "hạch toán vào TK511 nhưng không nằm trong báo cáo GCS\n"
                "- Hoặc do chênh lệch thời điểm ghi nhận doanh thu"
            )
            analysis["suggestion"] = (
                "1. Kiểm tra riêng doanh thu 4500TT và 1388DD trong sổ cái TK511\n"
                "2. Loại trừ 2 mã này ra khi so sánh với GCS\n"
                "3. So sánh lại: GCS = TK511 - 4500TT - 1388DD"
            )
        
        if not analysis["cause"]:
            analysis["cause"] = f"Chênh lệch {diff_value:,.0f} VND cần kiểm tra thủ công"
            analysis["suggestion"] = (
                "1. Kiểm tra lại từng bút toán trong kỳ\n"
                "2. So sánh chi tiết từng chứng từ giữa 2 nguồn dữ liệu\n"
                "3. Liên hệ bộ phận kế toán để xác nhận"
            )
        
        return analysis
