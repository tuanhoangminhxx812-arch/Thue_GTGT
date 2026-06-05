# -*- coding: utf-8 -*-
"""
Excel Export - Xuất kết quả ra file Excel.
"""

import io
import pandas as pd


def export_to_excel(data_dict, filename="bao_cao_doi_chieu.xlsx"):
    """
    Xuất tất cả dữ liệu đối chiếu ra file Excel với nhiều sheet.
    
    Args:
        data_dict: dict chứa các DataFrame cần xuất
        filename: tên file
    
    Returns:
        BytesIO buffer chứa file Excel
    """
    buffer = io.BytesIO()
    
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        workbook = writer.book
        
        # Formats
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#1B4F72',
            'font_color': 'white',
            'border': 1,
            'text_wrap': True,
            'valign': 'vcenter',
            'align': 'center',
        })
        
        number_format = workbook.add_format({
            'num_format': '#,##0',
            'border': 1,
        })
        
        total_format = workbook.add_format({
            'bold': True,
            'num_format': '#,##0',
            'border': 1,
            'bg_color': '#D5F5E3',
        })
        
        warning_format = workbook.add_format({
            'bg_color': '#FADBD8',
            'border': 1,
        })
        
        for sheet_name, df in data_dict.items():
            if isinstance(df, pd.DataFrame) and not df.empty:
                # Truncate sheet name to 31 chars (Excel limit)
                safe_name = sheet_name[:31]
                df.to_excel(writer, sheet_name=safe_name, index=False, startrow=1)
                
                worksheet = writer.sheets[safe_name]
                
                # Write headers
                for col_num, value in enumerate(df.columns):
                    worksheet.write(0, col_num, str(value), header_format)
                
                # Auto-fit columns
                for col_num, column in enumerate(df.columns):
                    max_length = max(
                        df[column].astype(str).map(len).max() if len(df) > 0 else 0,
                        len(str(column))
                    )
                    worksheet.set_column(col_num, col_num, min(max_length + 2, 40))
    
    buffer.seek(0)
    return buffer


def export_declaration_excel(declaration_df, tax_values, period="", filename="to_khai_thue_gtgt.xlsx"):
    """
    Xuất tờ khai thuế GTGT theo format chuẩn cơ quan thuế.
    
    Args:
        declaration_df: DataFrame chỉ tiêu tờ khai
        tax_values: dict các giá trị tính toán
        period: kỳ báo cáo (e.g., "04/2026")
    
    Returns:
        BytesIO buffer
    """
    buffer = io.BytesIO()
    
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        workbook = writer.book
        worksheet = workbook.add_worksheet('Tờ khai 01-GTGT')
        writer.sheets['Tờ khai 01-GTGT'] = worksheet
        
        # Formats
        title_format = workbook.add_format({
            'bold': True,
            'font_size': 14,
            'align': 'center',
            'font_color': '#1B4F72',
        })
        
        section_format = workbook.add_format({
            'bold': True,
            'font_size': 11,
            'bg_color': '#1B4F72',
            'font_color': 'white',
            'border': 1,
        })
        
        label_format = workbook.add_format({
            'border': 1,
            'text_wrap': True,
            'valign': 'vcenter',
        })
        
        code_format = workbook.add_format({
            'bold': True,
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
        })
        
        value_format = workbook.add_format({
            'num_format': '#,##0',
            'border': 1,
            'align': 'right',
            'valign': 'vcenter',
        })
        
        highlight_format = workbook.add_format({
            'bold': True,
            'num_format': '#,##0',
            'border': 1,
            'align': 'right',
            'bg_color': '#FDEBD0',
        })
        
        result_format = workbook.add_format({
            'bold': True,
            'num_format': '#,##0',
            'border': 2,
            'align': 'right',
            'bg_color': '#D5F5E3',
            'font_size': 12,
        })
        
        # Title
        worksheet.merge_range('A1:C1', 'TỜ KHAI THUẾ GIÁ TRỊ GIA TĂNG', title_format)
        worksheet.merge_range('A2:C2', f'(Mẫu số 01/GTGT) - Kỳ tính thuế: Tháng {period}', 
                             workbook.add_format({'align': 'center', 'italic': True}))
        
        # Column widths
        worksheet.set_column('A:A', 55)
        worksheet.set_column('B:B', 10)
        worksheet.set_column('C:C', 25)
        
        # Headers
        row = 3
        worksheet.write(row, 0, 'Chỉ tiêu', section_format)
        worksheet.write(row, 1, 'Mã số', section_format)
        worksheet.write(row, 2, 'Giá trị (VND)', section_format)
        
        # Data rows
        row = 4
        for _, item in declaration_df.iterrows():
            nhom = item.get("nhom", "")
            chi_tieu = item.get("chi_tieu", "")
            ma_so = item.get("ma_so", "")
            gia_tri = item.get("gia_tri", "")
            
            if nhom and not chi_tieu:
                # Section header
                worksheet.merge_range(row, 0, row, 2, nhom, section_format)
            else:
                worksheet.write(row, 0, chi_tieu, label_format)
                worksheet.write(row, 1, ma_so, code_format)
                
                # Highlight key values
                if ma_so in ["[37]", "[41]"]:
                    fmt = result_format
                elif ma_so in ["[35]", "[25]", "[36]"]:
                    fmt = highlight_format
                else:
                    fmt = value_format
                
                if isinstance(gia_tri, (int, float)):
                    worksheet.write_number(row, 2, gia_tri, fmt)
                else:
                    worksheet.write(row, 2, "", fmt)
            
            row += 1
        
        # Footer
        row += 1
        worksheet.write(row, 0, "Ghi chú: Số liệu này được tính toán tự động từ hệ thống kiểm dò thuế GTGT.",
                        workbook.add_format({'italic': True, 'font_color': '#888888'}))
    
    buffer.seek(0)
    return buffer
