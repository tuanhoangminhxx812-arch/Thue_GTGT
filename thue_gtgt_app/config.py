# -*- coding: utf-8 -*-
"""
Cấu hình ứng dụng Kiểm dò Thuế GTGT
Công ty Điện lực Vũng Tàu
"""

import os

# ============================================================
# ĐƯỜNG DẪN
# ============================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
STYLES_DIR = os.path.join(BASE_DIR, "styles")

# ============================================================
# MAPPING MÃ SẢN PHẨM → THUẾ SUẤT (%)
# ============================================================
TAX_RATE_MAP = {
    "DIEN01": 8,    # Điện kinh doanh/sinh hoạt
    "DIEN00": 0,    # Điện cho KH đặc thù (Nhôm Toàn Cầu)
    "CSPK02": 8,    # Công suất phản kháng (vô công)
    "CSPK00": 0,    # Vô công cho KH đặc thù
    "4500TT": 8,    # Cho thuê trụ điện
    "1388DD": 8,    # Điều động VTTB (mặc định 8%, có thể 10%)
    "5118QT": 0,    # Quyết toán (thường không phát sinh)
}

# Mapping mã sản phẩm → tên hiển thị
PRODUCT_NAME_MAP = {
    "DIEN01": "Điện",
    "DIEN00": "Điện (0%)",
    "CSPK02": "Điện vô công",
    "CSPK00": "Điện vô công (0%)",
    "4500TT": "Cho thuê trụ điện",
    "1388DD": "Điều động VTTB",
    "5118QT": "Quyết toán",
}

# Thứ tự hiển thị mã sản phẩm trên báo cáo
PRODUCT_DISPLAY_ORDER = ["DIEN00", "DIEN01", "CSPK00", "CSPK02", "1388DD", "5118QT", "4500TT"]

# ============================================================
# KHÁCH HÀNG ĐẶC THÙ (Thuế 0%)
# ============================================================
SPECIAL_CUSTOMERS = {
    "CT TNHH NHÔM TOÀN CẦU VIỆT NAM": {
        "tax_rate": 0,
        "product_codes": ["DIEN00", "CSPK00"],
        "description": "Khách hàng áp dụng thuế GTGT 0%",
    }
}

# ============================================================
# CẤU TRÚC CỘT CÁC BẢNG DỮ LIỆU
# ============================================================

# Báo cáo GCS
GCS_COLUMNS = [
    "stt", "ngay_ghi_so", "so_gcs", "so_hoa_don", "ngay_phat_hanh",
    "dien_nang_sh", "dien_nang_ngoai_sh", "dien_nang_tong",
    "tien_dien", "thue_dien", "tong_tien_dien",
    "tien_cspk", "thue_cspk", "tong_tien_cspk", "tong_cong", "extra"
]

# Sổ cái TK511
GL_TK511_COLUMNS = [
    "nguon_ps", "so_gd", "ngay_gd", "chi_nhanh", "trung_tam",
    "tai_khoan", "loai_hinh", "san_pham", "yeu_to", "don_vi_noi_bo",
    "du_phong_1", "du_phong_2", "loai_tien", "no_nguyen_te", "co_nguyen_te",
    "no_quy_doi", "co_quy_doi", "noi_dung", "trang_thai_hach_toan",
    "nguoi_tao", "nguoi_cap_nhat"
]

# Sổ cái TK3331 / TK1331
TA030_COLUMNS = [
    "ngay_ct", "so_ct", "nguon_ct", "dien_giai",
    "phat_sinh_no", "phat_sinh_co", "nguoi_hach_toan", "trang_thai"
]

# Bảng kê TA035 / TA036
BANGKE_COLUMNS = [
    "stt", "ky_hieu_hd", "so_hoa_don", "ngay_phat_hanh",
    "ten_doi_tac", "ma_so_thue", "mat_hang", "doanh_so",
    "thue_suat", "thue_gtgt", "ghi_chu", "nguon_ct",
    "so_ct", "ngay_lap_ct", "thoi_han_tt", "so_tien_da_tt",
    "loai_hinh_kd", "nguoi_lap_ct", "trang_thai"
]

# ============================================================
# TRẠNG THÁI CHỨNG TỪ
# ============================================================
STATUS_OK = ["Complete", "Cleared", "Posted"]
STATUS_WARNING = ["Draft"]
STATUS_ERROR = ["Unpost"]
STATUS_INFO = ["Not Reversed", "Reversed"]

# ============================================================
# LOẠI HÓA ĐƠN GCS
# ============================================================
GCS_INVOICE_TYPES = ["Hủy bỏ", "Lặp lại", "Phát sinh", "Thoái hoàn", "Truy thu"]

# ============================================================
# CHỈ TIÊU TỜ KHAI 01/GTGT
# ============================================================
TAX_DECLARATION_ITEMS = {
    22: "Thuế GTGT còn được khấu trừ kỳ trước chuyển sang",
    23: "Giá trị hàng hóa, dịch vụ mua vào",
    24: "Thuế GTGT của hàng hóa, dịch vụ mua vào",
    25: "Tổng số thuế GTGT được khấu trừ kỳ này",
    26: "Hàng hóa, dịch vụ bán ra không chịu thuế GTGT",
    27: "Hàng hóa, dịch vụ bán ra chịu thuế suất 0%",
    29: "Hàng hóa, dịch vụ bán ra chịu thuế suất 5%",
    30: "Thuế GTGT của HHDV bán ra chịu thuế suất 5%",
    32: "Hàng hóa, dịch vụ bán ra chịu thuế suất 8%",
    33: "Thuế GTGT của HHDV bán ra chịu thuế suất 8%",
    "32a": "Hàng hóa, dịch vụ bán ra chịu thuế suất 10%",
    "33a": "Thuế GTGT của HHDV bán ra chịu thuế suất 10%",
    34: "Tổng doanh số HHDV bán ra",
    35: "Tổng thuế GTGT của HHDV bán ra",
    36: "Thuế GTGT phát sinh trong kỳ (= [35] - [25])",
    37: "Thuế GTGT phải nộp trong kỳ",
    38: "Thuế GTGT chưa khấu trừ hết kỳ này",
    40: "Thuế GTGT đề nghị hoàn",
    41: "Thuế GTGT còn được khấu trừ chuyển kỳ sau",
    42: "Tổng doanh thu",
}

# ============================================================
# MÀU SẮC GIAO DIỆN
# ============================================================
COLORS = {
    "primary": "#1B4F72",       # EVN Blue
    "primary_light": "#2E86C1",
    "accent": "#00BCD4",
    "success": "#27AE60",
    "warning": "#F39C12",
    "danger": "#E74C3C",
    "info": "#3498DB",
    "bg_dark": "#0E1117",
    "bg_card": "#1E2A3A",
    "text_primary": "#FFFFFF",
    "text_secondary": "#B0BEC5",
}

# ============================================================
# CÁC FILE UPLOAD CẦN THIẾT
# ============================================================
REQUIRED_FILES = {
    "gcs": {
        "label": "📊 Báo cáo GCS (Hóa đơn phát hành)",
        "description": "File báo cáo tổng hợp GCS hàng tháng",
        "parser": "gcs_parser",
    },
    "gl_tk511": {
        "label": "📒 Sổ cái TK511 (Doanh thu)",
        "description": "Sổ cái tài khoản 511 - Doanh thu",
        "parser": "gl_parser",
    },
    "ta030_tk3331": {
        "label": "📗 Sổ cái TK3331 (Thuế đầu ra)",
        "description": "Sổ cái TK33311 - Thuế GTGT đầu ra",
        "parser": "ta030_parser",
    },
    "ta030_tk1331": {
        "label": "📕 Sổ cái TK1331 (Thuế đầu vào)",
        "description": "Sổ cái TK13311 - Thuế GTGT đầu vào",
        "parser": "ta030_parser",
    },
    "ta035": {
        "label": "📋 Bảng kê TA035 (Bán ra)",
        "description": "Bảng kê hóa đơn hàng hóa, dịch vụ bán ra",
        "parser": "ta035_parser",
    },
    "ta036": {
        "label": "📝 Bảng kê TA036 (Mua vào)",
        "description": "Bảng kê hóa đơn hàng hóa, dịch vụ mua vào",
        "parser": "ta036_parser",
    },
}

OPTIONAL_FILES = {
    "nhom_tc": {
        "label": "🏭 Chi tiết Nhôm Toàn Cầu",
        "description": "Báo cáo chi tiết khách hàng Nhôm Toàn Cầu (DIEN00)",
        "parser": "nhom_tc_parser",
    },
    "gcs_prev": {
        "label": "📊 GCS tháng trước (sang tháng hiện tại)",
        "description": "File GCS tháng trước để so sánh chênh lệch",
        "parser": "gcs_parser",
    },
}
