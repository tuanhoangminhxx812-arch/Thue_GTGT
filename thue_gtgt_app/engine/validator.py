# -*- coding: utf-8 -*-
"""
Validation Engine - Kiểm dò và xác thực hợp lệ chứng từ.
Module 2: Kiểm tra trạng thái, đối chiếu doanh thu, phân loại thuế suất.
"""

import pandas as pd
from config import STATUS_OK, STATUS_WARNING, STATUS_ERROR, STATUS_INFO, TAX_RATE_MAP


class ValidationEngine:
    """Động cơ kiểm dò và xác thực dữ liệu kế toán."""
    
    def __init__(self, data_store):
        """
        Args:
            data_store: dict chứa tất cả dữ liệu đã parse từ các module.
        """
        self.data = data_store
        self.results = []
        self.warnings = []
        self.errors = []
    
    def run_all_checks(self):
        """Chạy tất cả các kiểm tra."""
        self.results = []
        self.warnings = []
        self.errors = []
        
        self.check_document_status()
        self.check_revenue_reconciliation()
        self.check_tax_rate_classification()
        self.check_output_tax_reconciliation()
        self.check_input_tax_reconciliation()
        
        return {
            "results": self.results,
            "warnings": self.warnings,
            "errors": self.errors,
            "summary": self._get_summary(),
        }
    
    def check_document_status(self):
        """Kiểm tra trạng thái chứng từ Draft/Unpost."""
        check_name = "Kiểm tra trạng thái chứng từ"
        
        # Kiểm tra TK3331 (thuế đầu ra)
        tk3331_data = self.data.get("ta030_tk3331", {}).get("data", pd.DataFrame())
        if not tk3331_data.empty and "trang_thai" in tk3331_data.columns:
            draft_rows = tk3331_data[tk3331_data["trang_thai"] == "Draft"]
            unpost_rows = tk3331_data[tk3331_data["trang_thai"] == "Unpost"]
            
            if not draft_rows.empty:
                total_co = draft_rows["phat_sinh_co"].sum()
                self.warnings.append({
                    "check": check_name,
                    "source": "Sổ cái TK3331 (Thuế đầu ra)",
                    "message": f"Có {len(draft_rows)} chứng từ trạng thái DRAFT (chưa ghi sổ)",
                    "detail": f"Tổng PS Có: {total_co:,.0f} VND",
                    "severity": "warning",
                    "data": draft_rows,
                })
            
            if not unpost_rows.empty:
                total_co = unpost_rows["phat_sinh_co"].sum()
                total_no = unpost_rows["phat_sinh_no"].sum()
                self.errors.append({
                    "check": check_name,
                    "source": "Sổ cái TK3331 (Thuế đầu ra)",
                    "message": f"Có {len(unpost_rows)} chứng từ trạng thái UNPOST",
                    "detail": f"Tổng PS Có: {total_co:,.0f} | PS Nợ: {total_no:,.0f} VND",
                    "severity": "error",
                    "suggestion": "Kiểm tra và post lại các chứng từ Unpost trước khi chốt sổ. "
                                  "Có thể lệch do chứng từ Unpost ở TK 33311 chưa được ghi sổ.",
                    "data": unpost_rows,
                })
        
        # Kiểm tra TK1331 (thuế đầu vào)
        tk1331_data = self.data.get("ta030_tk1331", {}).get("data", pd.DataFrame())
        if not tk1331_data.empty and "trang_thai" in tk1331_data.columns:
            draft_rows = tk1331_data[tk1331_data["trang_thai"] == "Draft"]
            unpost_rows = tk1331_data[tk1331_data["trang_thai"] == "Unpost"]
            
            if not draft_rows.empty:
                total_no = draft_rows["phat_sinh_no"].sum()
                self.warnings.append({
                    "check": check_name,
                    "source": "Sổ cái TK1331 (Thuế đầu vào)",
                    "message": f"Có {len(draft_rows)} chứng từ trạng thái DRAFT",
                    "detail": f"Tổng PS Nợ: {total_no:,.0f} VND",
                    "severity": "warning",
                    "data": draft_rows,
                })
            
            if not unpost_rows.empty:
                total_no = unpost_rows["phat_sinh_no"].sum()
                self.errors.append({
                    "check": check_name,
                    "source": "Sổ cái TK1331 (Thuế đầu vào)",
                    "message": f"Có {len(unpost_rows)} chứng từ trạng thái UNPOST",
                    "detail": f"Tổng PS Nợ: {total_no:,.0f} VND",
                    "severity": "error",
                    "suggestion": "Lệch do có chứng từ Unpost ở TK 13311 chưa ghi sổ. "
                                  "Cần post lại hoặc reverse chứng từ này.",
                    "data": unpost_rows,
                })
        
        self.results.append({
            "check": check_name,
            "status": "error" if self.errors else ("warning" if self.warnings else "pass"),
            "message": f"Tìm thấy {len(self.errors)} lỗi, {len(self.warnings)} cảnh báo",
        })
    
    def check_revenue_reconciliation(self):
        """Đối chiếu doanh thu GCS vs TK511."""
        check_name = "Đối chiếu Doanh thu (GCS vs TK511)"
        
        gcs_data = self.data.get("gcs", {})
        gl_data = self.data.get("gl_tk511", {})
        
        if not gcs_data or not gl_data:
            self.results.append({
                "check": check_name,
                "status": "skip",
                "message": "Thiếu dữ liệu GCS hoặc TK511",
            })
            return
        
        gcs_totals = gcs_data.get("totals", {})
        gl_by_product = gl_data.get("by_product", pd.DataFrame())
        
        if gcs_totals and not gl_by_product.empty:
            # Tổng doanh thu GCS (tiền điện)
            gcs_tien_dien = gcs_totals.get("tien_dien", 0)
            gcs_tien_cspk = gcs_totals.get("tien_cspk", 0)
            
            # Tổng phát sinh Có TK511 theo mã
            gl_dien = gl_by_product[gl_by_product["ma_san_pham"].isin(["DIEN01", "DIEN00"])]
            gl_cspk = gl_by_product[gl_by_product["ma_san_pham"].isin(["CSPK02", "CSPK00"])]
            
            gl_tien_dien = gl_dien["tong_co"].sum() if not gl_dien.empty else 0
            gl_tien_cspk = gl_cspk["tong_co"].sum() if not gl_cspk.empty else 0
            
            # Tính chênh lệch
            clech_dien = gcs_tien_dien - gl_tien_dien
            clech_cspk = gcs_tien_cspk - gl_tien_cspk
            
            result = {
                "check": check_name,
                "details": {
                    "GCS - Tiền điện": f"{gcs_tien_dien:,.0f}",
                    "TK511 - Tiền điện": f"{gl_tien_dien:,.0f}",
                    "Chênh lệch điện": f"{clech_dien:,.0f}",
                    "GCS - CSPK": f"{gcs_tien_cspk:,.0f}",
                    "TK511 - CSPK": f"{gl_tien_cspk:,.0f}",
                    "Chênh lệch CSPK": f"{clech_cspk:,.0f}",
                },
            }
            
            if clech_dien == 0 and clech_cspk == 0:
                result["status"] = "pass"
                result["message"] = "✅ Khớp hoàn toàn"
            else:
                result["status"] = "warning"
                result["message"] = f"⚠️ Chênh lệch: Điện {clech_dien:,.0f} | CSPK {clech_cspk:,.0f}"
                if clech_dien != 0:
                    self.warnings.append({
                        "check": check_name,
                        "source": "GCS vs TK511",
                        "message": f"Chênh lệch tiền điện: {clech_dien:,.0f} VND",
                        "severity": "warning",
                        "suggestion": "Kiểm tra có giao dịch 4500TT (cho thuê trụ điện) hoặc 1388DD "
                                      "(điều động VTTB) hạch toán vào TK511 nhưng không nằm trong GCS.",
                    })
            
            self.results.append(result)
    
    def check_tax_rate_classification(self):
        """Kiểm tra phân loại thuế suất đúng quy định."""
        check_name = "Phân loại thuế suất"
        
        ta035_data = self.data.get("ta035", {}).get("data", pd.DataFrame())
        
        if ta035_data.empty:
            self.results.append({
                "check": check_name,
                "status": "skip",
                "message": "Thiếu dữ liệu TA035",
            })
            return
        
        issues = []
        
        for _, row in ta035_data.iterrows():
            mat_hang = str(row.get("mat_hang", "")).upper()
            thue_suat = row.get("thue_suat", 0)
            expected_rate = TAX_RATE_MAP.get(mat_hang, None)
            
            if expected_rate is not None and thue_suat != expected_rate:
                # Trường hợp đặc biệt: 1388DD có thể là 8% hoặc 10%
                if mat_hang == "1388DD" and thue_suat in [8, 10]:
                    continue
                
                issues.append({
                    "mat_hang": mat_hang,
                    "thue_suat_thuc_te": thue_suat,
                    "thue_suat_ky_vong": expected_rate,
                    "ten": row.get("ten_nguoi_mua", ""),
                    "doanh_so": row.get("doanh_so", 0),
                })
        
        # Kiểm tra Nhôm Toàn Cầu phải là 0%
        nhom_tc_rows = ta035_data[
            ta035_data["ghi_chu"].str.contains("NHÔM TOÀN CẦU", case=False, na=False) |
            ta035_data["ten_nguoi_mua"].str.contains("NHÔM TOÀN CẦU", case=False, na=False)
        ]
        
        for _, row in nhom_tc_rows.iterrows():
            if row.get("thue_suat", 0) != 0:
                issues.append({
                    "mat_hang": row.get("mat_hang", ""),
                    "thue_suat_thuc_te": row.get("thue_suat", 0),
                    "thue_suat_ky_vong": 0,
                    "ten": "CT TNHH NHÔM TOÀN CẦU VIỆT NAM",
                    "doanh_so": row.get("doanh_so", 0),
                })
        
        if issues:
            self.errors.append({
                "check": check_name,
                "source": "Bảng kê TA035",
                "message": f"Có {len(issues)} hóa đơn áp dụng sai thuế suất",
                "severity": "error",
                "suggestion": "Kiểm tra lại mã hàng hóa và thuế suất tương ứng trên từng hóa đơn.",
                "data": pd.DataFrame(issues),
            })
            self.results.append({
                "check": check_name,
                "status": "error",
                "message": f"❌ {len(issues)} hóa đơn sai thuế suất",
            })
        else:
            self.results.append({
                "check": check_name,
                "status": "pass",
                "message": "✅ Tất cả thuế suất đều đúng quy định",
            })
    
    def check_output_tax_reconciliation(self):
        """Đối chiếu thuế đầu ra: TA030 (TK3331) vs TA035."""
        check_name = "Đối chiếu Thuế đầu ra (TK3331 vs TA035)"
        
        ta030 = self.data.get("ta030_tk3331", {})
        ta035 = self.data.get("ta035", {})
        
        if not ta030 or not ta035:
            self.results.append({
                "check": check_name,
                "status": "skip",
                "message": "Thiếu dữ liệu TK3331 hoặc TA035",
            })
            return
        
        ta030_total_co = ta030.get("totals", {}).get("tong_co", 0)
        ta035_total_thue = ta035.get("totals", {}).get("tong_thue_gtgt", 0)
        
        clech = ta030_total_co - ta035_total_thue
        
        result = {
            "check": check_name,
            "details": {
                "Sổ cái TK3331 (PS Có)": f"{ta030_total_co:,.0f}",
                "Bảng kê TA035 (Thuế GTGT)": f"{ta035_total_thue:,.0f}",
                "Chênh lệch": f"{clech:,.0f}",
            },
        }
        
        if clech == 0:
            result["status"] = "pass"
            result["message"] = "✅ Khớp hoàn toàn"
        else:
            result["status"] = "warning"
            result["message"] = f"⚠️ Chênh lệch: {clech:,.0f} VND"
            self.warnings.append({
                "check": check_name,
                "source": "TK3331 vs TA035",
                "message": f"Chênh lệch thuế đầu ra: {clech:,.0f} VND",
                "severity": "warning",
                "suggestion": "Kiểm tra các chứng từ Unpost/Draft trong sổ cái TK3331. "
                              "Chênh lệch có thể do chứng từ giải trừ thuế hoặc kết chuyển chưa ghi sổ.",
            })
        
        self.results.append(result)
    
    def check_input_tax_reconciliation(self):
        """Đối chiếu thuế đầu vào: TA036 vs TA030 (TK1331)."""
        check_name = "Đối chiếu Thuế đầu vào (TA036 vs TK1331)"
        
        ta036 = self.data.get("ta036", {})
        ta030 = self.data.get("ta030_tk1331", {})
        
        if not ta036 or not ta030:
            self.results.append({
                "check": check_name,
                "status": "skip",
                "message": "Thiếu dữ liệu TA036 hoặc TK1331",
            })
            return
        
        ta036_total_thue = ta036.get("totals", {}).get("tong_thue_gtgt", 0)
        ta030_total_no = ta030.get("totals", {}).get("tong_no", 0)
        # Trừ đi dư đầu kỳ vì PS Nợ bao gồm dư ĐK
        opening = ta030.get("opening_balance", 0)
        ta030_ps_no = ta030_total_no - opening if ta030_total_no > opening else ta030_total_no
        
        clech = ta036_total_thue - ta030_ps_no
        
        result = {
            "check": check_name,
            "details": {
                "Bảng kê TA036 (Thuế GTGT)": f"{ta036_total_thue:,.0f}",
                "Sổ cái TK1331 (PS Nợ)": f"{ta030_ps_no:,.0f}",
                "Chênh lệch": f"{clech:,.0f}",
            },
        }
        
        if clech == 0:
            result["status"] = "pass"
            result["message"] = "✅ Khớp hoàn toàn"
        else:
            result["status"] = "warning"
            result["message"] = f"⚠️ Chênh lệch: {clech:,.0f} VND"
            self.warnings.append({
                "check": check_name,
                "source": "TA036 vs TK1331",
                "message": f"Chênh lệch thuế đầu vào: {clech:,.0f} VND",
                "severity": "warning",
                "suggestion": "Kiểm tra các chứng từ Not Reversed hoặc Unpost trong sổ cái TK1331. "
                              "Chênh lệch có thể do kết chuyển VAT TK13313 qua TK33311.",
            })
        
        self.results.append(result)
    
    def _get_summary(self):
        """Tạo báo cáo tóm tắt."""
        total_checks = len(self.results)
        passed = sum(1 for r in self.results if r["status"] == "pass")
        warnings = sum(1 for r in self.results if r["status"] == "warning")
        errors = sum(1 for r in self.results if r["status"] == "error")
        skipped = sum(1 for r in self.results if r["status"] == "skip")
        
        return {
            "total_checks": total_checks,
            "passed": passed,
            "warnings": warnings,
            "errors": errors,
            "skipped": skipped,
            "overall_status": "error" if errors > 0 else ("warning" if warnings > 0 else "pass"),
        }
