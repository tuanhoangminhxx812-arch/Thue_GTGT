# -*- coding: utf-8 -*-
"""
Module 4: Tờ khai Thuế GTGT (Tax Declaration Output).
Trích xuất số liệu lên tờ khai mẫu 01/GTGT và xuất Excel/XML.
"""

import streamlit as st
import pandas as pd
from engine.tax_calculator import TaxCalculator
from export.excel_export import export_declaration_excel, export_to_excel
from export.xml_export import export_to_xml, get_xml_bytes


def render_export_module():
    """Render Module 4: Tờ khai thuế GTGT."""
    
    st.markdown("""
    <h1 style="
        background: linear-gradient(135deg, #00BCD4, #2E86C1, #1B4F72);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800; font-size: 1.8rem; margin-bottom: 5px;
    ">📋 Tờ Khai Thuế GTGT</h1>
    <p style="color: #78909C; font-size: 0.9rem; margin-bottom: 20px;">
        Tổng hợp chỉ tiêu tờ khai mẫu 01/GTGT — Sẵn sàng điền vào phần mềm HTKK
    </p>
    """, unsafe_allow_html=True)
    
    data_store = st.session_state.get("data_store", {})
    period = st.session_state.get("period", "")
    khau_tru = st.session_state.get("khau_tru_ky_truoc", 0)
    
    if not data_store:
        st.warning("⚠️ Chưa có dữ liệu. Vui lòng upload file ở **Module 1** trước.")
        return
    
    # Calculate
    calculator = TaxCalculator(data_store, khau_tru_ky_truoc=khau_tru)
    tax_values = calculator.calculate()
    declaration_df = calculator.get_declaration_table()
    
    # ============ SUMMARY METRICS ============
    st.markdown("### 💰 Kết quả chính")
    
    c1, c2, c3, c4 = st.columns(4)
    
    with c1:
        val_35 = tax_values.get(35, 0)
        st.metric(
            "Tổng thuế GTGT đầu ra [35]",
            f"{val_35:,.0f}",
            help="Tổng thuế GTGT của HHDV bán ra"
        )
    
    with c2:
        val_25 = tax_values.get(25, 0)
        st.metric(
            "Tổng thuế được khấu trừ [25]",
            f"{val_25:,.0f}",
            help="Tổng thuế GTGT được khấu trừ kỳ này"
        )
    
    with c3:
        val_37 = tax_values.get(37, 0)
        delta_color = "normal" if val_37 > 0 else "off"
        st.metric(
            "Thuế phải nộp [37]",
            f"{val_37:,.0f}",
        )
    
    with c4:
        val_41 = tax_values.get(41, 0)
        st.metric(
            "Khấu trừ chuyển kỳ sau [41]",
            f"{val_41:,.0f}",
        )
    
    # Highlight result
    val_36 = tax_values.get(36, 0)
    if val_36 >= 0:
        st.success(f"""
        🏦 **Thuế GTGT phải nộp trong kỳ Tháng {period}: {val_36:,.0f} VND**
        
        Thuế đầu ra ({val_35:,.0f}) - Thuế được khấu trừ ({val_25:,.0f}) = **{val_36:,.0f} VND**
        """)
    else:
        st.info(f"""
        📋 **Thuế GTGT còn được khấu trừ chuyển kỳ sau: {abs(val_36):,.0f} VND**
        
        Thuế đầu ra ({val_35:,.0f}) - Thuế được khấu trừ ({val_25:,.0f}) = **{val_36:,.0f} VND**
        """)
    
    # ============ DECLARATION TABLE ============
    st.markdown("---")
    st.markdown(f"### 📄 Tờ khai mẫu số 01/GTGT — Tháng {period}")
    
    # Display declaration table with styling
    display_df = declaration_df.copy()
    
    def style_declaration(row):
        nhom = row.get("nhom", "")
        ma_so = row.get("ma_so", "")
        
        if nhom and not row.get("chi_tieu", ""):
            return ['background-color: #1B4F72; color: white; font-weight: bold'] * len(row)
        
        if ma_so in ["[37]", "[41]"]:
            return ['background-color: rgba(39,174,96,0.15); font-weight: bold'] * len(row)
        elif ma_so in ["[35]", "[25]", "[36]"]:
            return ['background-color: rgba(243,156,18,0.1); font-weight: bold'] * len(row)
        
        return [''] * len(row)
    
    # Format display
    display_df2 = display_df[["chi_tieu", "ma_so", "gia_tri"]].copy()
    display_df2.columns = ["Chỉ tiêu", "Mã số", "Giá trị (VND)"]
    
    # Format numbers
    def fmt_value(v):
        if isinstance(v, (int, float)):
            if v == 0:
                return "-"
            return f"{v:,.0f}"
        return str(v)
    
    display_df2["Giá trị (VND)"] = display_df2["Giá trị (VND)"].apply(fmt_value)
    
    # Add section headers back
    styled_rows = []
    for _, row in declaration_df.iterrows():
        nhom = row.get("nhom", "")
        if nhom and not row.get("chi_tieu", ""):
            styled_rows.append({
                "Chỉ tiêu": f"**{nhom}**",
                "Mã số": "",
                "Giá trị (VND)": "",
            })
        else:
            styled_rows.append({
                "Chỉ tiêu": row.get("chi_tieu", ""),
                "Mã số": row.get("ma_so", ""),
                "Giá trị (VND)": fmt_value(row.get("gia_tri", "")),
            })
    
    final_df = pd.DataFrame(styled_rows)
    
    st.dataframe(
        final_df,
        use_container_width=True,
        height=600,
        hide_index=True,
        column_config={
            "Chỉ tiêu": st.column_config.TextColumn("Chỉ tiêu", width="large"),
            "Mã số": st.column_config.TextColumn("Mã số", width="small"),
            "Giá trị (VND)": st.column_config.TextColumn("Giá trị (VND)", width="medium"),
        }
    )
    
    # ============ EXPORT BUTTONS ============
    st.markdown("---")
    st.markdown("### 📤 Xuất kết quả")
    
    col_exp1, col_exp2, col_exp3 = st.columns(3)
    
    with col_exp1:
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #1a3a2a, #1a4a3a);
            border: 1px solid #27AE60;
            border-radius: 12px;
            padding: 16px;
            text-align: center;
        ">
            <span style="font-size: 2rem;">📊</span>
            <p style="color: #27AE60; font-weight: 600; margin: 8px 0 4px 0;">
                Export Excel
            </p>
            <p style="color: #78909C; font-size: 0.75rem; margin: 0;">
                Tờ khai theo format chuẩn cơ quan Thuế
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        excel_buffer = export_declaration_excel(
            declaration_df, tax_values, period,
            filename=f"to_khai_01GTGT_T{period.replace('/', '_')}.xlsx"
        )
        st.download_button(
            "⬇️ Tải file Excel",
            data=excel_buffer,
            file_name=f"to_khai_01GTGT_T{period.replace('/', '_')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
    
    with col_exp2:
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #1a2a3a, #1a3a5a);
            border: 1px solid #2E86C1;
            border-radius: 12px;
            padding: 16px;
            text-align: center;
        ">
            <span style="font-size: 2rem;">📝</span>
            <p style="color: #2E86C1; font-weight: 600; margin: 8px 0 4px 0;">
                Export XML
            </p>
            <p style="color: #78909C; font-size: 0.75rem; margin: 0;">
                File XML nhập vào phần mềm HTKK
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        xml_str = export_to_xml(tax_values, period)
        xml_bytes = get_xml_bytes(xml_str)
        st.download_button(
            "⬇️ Tải file XML",
            data=xml_bytes,
            file_name=f"to_khai_01GTGT_T{period.replace('/', '_')}.xml",
            mime="application/xml",
            use_container_width=True,
        )
    
    with col_exp3:
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #3a2a1a, #4a3a1a);
            border: 1px solid #F39C12;
            border-radius: 12px;
            padding: 16px;
            text-align: center;
        ">
            <span style="font-size: 2rem;">📦</span>
            <p style="color: #F39C12; font-weight: 600; margin: 8px 0 4px 0;">
                Export Đối chiếu
            </p>
            <p style="color: #78909C; font-size: 0.75rem; margin: 0;">
                Toàn bộ bảng đối chiếu TAX_VTA
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Prepare reconciliation data for export
        from engine.reconciler import ReconciliationEngine
        recon_engine = ReconciliationEngine(data_store)
        
        export_data = {}
        summary = recon_engine.build_summary_table()
        if not summary.empty:
            export_data["Tong_hop_theo_ma"] = summary
        
        tax_output = recon_engine.build_tax_output_table()
        if not tax_output.empty:
            export_data["Thue_dau_ra"] = tax_output
        
        # Add declaration
        export_data["To_khai_01GTGT"] = declaration_df[["chi_tieu", "ma_so", "gia_tri"]]
        
        if export_data:
            recon_buffer = export_to_excel(
                export_data,
                filename=f"doi_chieu_T{period.replace('/', '_')}.xlsx"
            )
            st.download_button(
                "⬇️ Tải file Excel",
                data=recon_buffer,
                file_name=f"doi_chieu_TAX_VTA_T{period.replace('/', '_')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
    
    # ============ DETAIL BREAKDOWN ============
    st.markdown("---")
    st.markdown("### 📊 Chi tiết theo thuế suất")
    
    detail_cols = st.columns(3)
    
    with detail_cols[0]:
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #1e2a3a, #263d55);
            border: 1px solid rgba(0,188,212,0.2);
            border-radius: 12px; padding: 16px;
        ">
            <p style="color: #00BCD4; font-weight: 600; margin: 0;">
                🏷️ Thuế suất 0%
            </p>
        </div>
        """, unsafe_allow_html=True)
        st.metric("Doanh số [27]", f"{tax_values.get(27, 0):,.0f}")
        st.caption("DIEN00, CSPK00 (Nhôm Toàn Cầu)")
    
    with detail_cols[1]:
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #1e2a3a, #263d55);
            border: 1px solid rgba(0,188,212,0.2);
            border-radius: 12px; padding: 16px;
        ">
            <p style="color: #F39C12; font-weight: 600; margin: 0;">
                🏷️ Thuế suất 8%
            </p>
        </div>
        """, unsafe_allow_html=True)
        st.metric("Doanh số [32]", f"{tax_values.get(32, 0):,.0f}")
        st.metric("Thuế GTGT [33]", f"{tax_values.get(33, 0):,.0f}")
        st.caption("DIEN01, CSPK02, 4500TT, 1388DD")
    
    with detail_cols[2]:
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #1e2a3a, #263d55);
            border: 1px solid rgba(0,188,212,0.2);
            border-radius: 12px; padding: 16px;
        ">
            <p style="color: #E74C3C; font-weight: 600; margin: 0;">
                🏷️ Thuế suất 10%
            </p>
        </div>
        """, unsafe_allow_html=True)
        st.metric("Doanh số [32a]", f"{tax_values.get('32a', 0):,.0f}")
        st.metric("Thuế GTGT [33a]", f"{tax_values.get('33a', 0):,.0f}")
        st.caption("1388DD (một phần)")
