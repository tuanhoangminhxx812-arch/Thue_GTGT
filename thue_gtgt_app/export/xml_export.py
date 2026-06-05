# -*- coding: utf-8 -*-
"""
XML Export - Xuất file XML theo chuẩn HTKK (Tờ khai 01/GTGT).
"""

import xml.etree.ElementTree as ET
from xml.dom import minidom
import io


def export_to_xml(tax_values, period="", company_info=None):
    """
    Xuất tờ khai thuế GTGT dạng XML theo chuẩn HTKK.
    
    Args:
        tax_values: dict chỉ tiêu tờ khai (key = mã số, value = giá trị)
        period: kỳ tính thuế (e.g., "04/2026")
        company_info: dict thông tin doanh nghiệp
    
    Returns:
        str: nội dung XML
    """
    if company_info is None:
        company_info = {
            "ma_so_thue": "0300951119-010",
            "ten_nguoi_nop_thue": "CHI NHÁNH TỔNG CÔNG TY ĐIỆN LỰC TP.HCM - CÔNG TY ĐIỆN LỰC VŨNG TÀU",
            "dia_chi": "60 Trần Hưng Đạo, Phường 1, TP Vũng Tàu, Tỉnh Bà Rịa - Vũng Tàu",
        }
    
    # Root element
    root = ET.Element("HSoThueDTu")
    root.set("xmlns", "http://kekhaithue.gdt.gov.vn")
    
    # Header
    header = ET.SubElement(root, "HSoKhaiThue")
    
    tt_chung = ET.SubElement(header, "TTinChung")
    
    mst = ET.SubElement(tt_chung, "MST")
    mst.text = company_info.get("ma_so_thue", "")
    
    ten = ET.SubElement(tt_chung, "TenNNT")
    ten.text = company_info.get("ten_nguoi_nop_thue", "")
    
    dia_chi = ET.SubElement(tt_chung, "DChiNNT")
    dia_chi.text = company_info.get("dia_chi", "")
    
    ky_tinh_thue = ET.SubElement(tt_chung, "KyTinhThue")
    if "/" in period:
        parts = period.split("/")
        thang = ET.SubElement(ky_tinh_thue, "Thang")
        thang.text = parts[0]
        nam = ET.SubElement(ky_tinh_thue, "Nam")
        nam.text = parts[1]
    
    ma_mau = ET.SubElement(tt_chung, "MaMauBieu")
    ma_mau.text = "01/GTGT"
    
    # Chi tiết tờ khai
    ct_tokhai = ET.SubElement(header, "CTieuTKhai")
    
    # Map chỉ tiêu
    chi_tieu_map = {
        22: "ct22",
        23: "ct23",
        24: "ct24",
        25: "ct25",
        26: "ct26",
        27: "ct27",
        29: "ct29",
        30: "ct30",
        32: "ct32",
        33: "ct33",
        "32a": "ct32a",
        "33a": "ct33a",
        34: "ct34",
        35: "ct35",
        36: "ct36",
        37: "ct37",
        38: "ct38",
        40: "ct40",
        41: "ct41",
        42: "ct42",
    }
    
    for key, xml_tag in chi_tieu_map.items():
        value = tax_values.get(key, 0)
        elem = ET.SubElement(ct_tokhai, xml_tag)
        elem.text = str(int(value)) if isinstance(value, (int, float)) else "0"
    
    # Format XML
    xml_str = ET.tostring(root, encoding='unicode', xml_declaration=False)
    
    # Pretty print
    try:
        dom = minidom.parseString(f'<?xml version="1.0" encoding="UTF-8"?>\n{xml_str}')
        pretty_xml = dom.toprettyxml(indent="  ", encoding=None)
        # Remove extra declaration
        lines = pretty_xml.split('\n')
        if lines[0].startswith('<?xml'):
            lines[0] = '<?xml version="1.0" encoding="UTF-8"?>'
        return '\n'.join(lines)
    except Exception:
        return f'<?xml version="1.0" encoding="UTF-8"?>\n{xml_str}'


def get_xml_bytes(xml_string):
    """Convert XML string to bytes for download."""
    return xml_string.encode('utf-8')
