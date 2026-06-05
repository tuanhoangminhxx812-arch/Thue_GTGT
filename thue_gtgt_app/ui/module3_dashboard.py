# -*- coding: utf-8 -*-
"""
Module 3: Dashboard Đối chiếu (Mẫu TAX_VTA).
Hiển thị bảng tổng hợp đối chiếu và phân tích chênh lệch.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from engine.reconciler import ReconciliationEngine


def render_dashboard_module():
    """Render Module 3: Dashboard đối chiếu TAX_VTA."""
    
    st.markdown("""
    <h1 style="
        background: linear-gradient(135deg, #00BCD4, #2E86C1, #1B4F72);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800; font-size: 1.8rem; margin-bottom: 5px;
    ">📊 Đối Chiếu Tự Động</h1>
    <p style="color: #78909C; font-size: 0.9rem; margin-bottom: 20px;">
        Bảng đối chiếu tổng hợp theo mẫu TAX_VTA — Doanh số và Tiền thuế theo từng mã
    </p>
    """, unsafe_allow_html=True)
    
    data_store = st.session_state.get("data_store", {})
    
    if not data_store:
        st.warning("⚠️ Chưa có dữ liệu. Vui lòng upload file ở **Module 1** trước.")
        return
    
    period = st.session_state.get("period", "")
    engine = ReconciliationEngine(data_store)
    
    # ============ TAB LAYOUT ============
    tab1, tab2, tab3 = st.tabs([
        "📊 Tổng hợp theo mã",
        "💰 Thuế đầu ra lên tờ khai",
        "🔄 Đối chiếu chéo"
    ])
    
    # ============ TAB 1: TỔNG HỢP THEO MÃ ============
    with tab1:
        st.markdown(f"#### Bảng tổng hợp Doanh số & Tiền thuế — Tháng {period}")
        
        summary_table = engine.build_summary_table()
        
        if summary_table.empty:
            st.info("📭 Chưa đủ dữ liệu để tạo bảng tổng hợp. Cần upload TA035 và GCS.")
        else:
            # Format columns
            display_df = summary_table.copy()
            display_df.columns = [
                "Mã", "TA035\nDoanh số", "TA035\nTiền thuế",
                "GCS\nDoanh số", "GCS\nTiền thuế",
                "Chênh lệch\nDoanh số", "Chênh lệch\nTiền thuế"
            ]
            
            # Styling
            def style_diff(val):
                if isinstance(val, (int, float)):
                    if val != 0:
                        return 'color: #E74C3C; font-weight: bold; background-color: rgba(231,76,60,0.1)'
                    else:
                        return 'color: #27AE60; font-weight: bold'
                return ''
            
            def style_row(row):
                styles = [''] * len(row)
                if row.iloc[0] == "Cộng":
                    styles = ['font-weight: bold; background-color: rgba(0,188,212,0.1)'] * len(row)
                return styles
            
            num_cols = display_df.columns[1:]
            format_dict = {col: "{:,.0f}" for col in num_cols}
            
            styled = display_df.style\
                .apply(style_row, axis=1)\
                .applymap(style_diff, subset=["Chênh lệch\nDoanh số", "Chênh lệch\nTiền thuế"])\
                .format(format_dict, na_rep="-")
            
            st.dataframe(styled, use_container_width=True, height=400)
            
            # Chart
            chart_data = summary_table[summary_table["ma"] != "Cộng"].copy()
            if not chart_data.empty:
                st.markdown("---")
                
                c1, c2 = st.columns(2)
                
                with c1:
                    fig = go.Figure()
                    fig.add_trace(go.Bar(
                        name='TA035',
                        x=chart_data['ma'],
                        y=chart_data['ta035_doanh_so'],
                        marker_color='#2E86C1',
                    ))
                    fig.add_trace(go.Bar(
                        name='GCS',
                        x=chart_data['ma'],
                        y=chart_data['gcs_doanh_so'],
                        marker_color='#00BCD4',
                    ))
                    fig.update_layout(
                        title="Doanh số theo mã (TA035 vs GCS)",
                        barmode='group',
                        template='plotly_dark',
                        height=350,
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        font=dict(family="Inter"),
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                with c2:
                    fig2 = go.Figure()
                    fig2.add_trace(go.Bar(
                        name='TA035',
                        x=chart_data['ma'],
                        y=chart_data['ta035_thue'],
                        marker_color='#F39C12',
                    ))
                    fig2.add_trace(go.Bar(
                        name='GCS',
                        x=chart_data['ma'],
                        y=chart_data['gcs_thue'],
                        marker_color='#E74C3C',
                    ))
                    fig2.update_layout(
                        title="Tiền thuế theo mã (TA035 vs GCS)",
                        barmode='group',
                        template='plotly_dark',
                        height=350,
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        font=dict(family="Inter"),
                    )
                    st.plotly_chart(fig2, use_container_width=True)
    
    # ============ TAB 2: THUẾ ĐẦU RA LÊN TỜ KHAI ============
    with tab2:
        st.markdown(f"#### Thuế đầu ra lên Tờ khai — Tháng {period}")
        
        tax_output_table = engine.build_tax_output_table()
        
        if tax_output_table.empty:
            st.info("📭 Chưa đủ dữ liệu. Cần upload TA035.")
        else:
            display_df2 = tax_output_table.copy()
            display_df2.columns = [
                "Loại", "Mã", "Doanh số", "Thuế suất (%)",
                "Tiền thuế", "Sau thuế"
            ]
            
            def style_total(row):
                if row["Mã"] == "Tổng cộng":
                    return ['font-weight: bold; background-color: rgba(0,188,212,0.15)'] * len(row)
                return [''] * len(row)
            
            num_cols2 = ["Doanh số", "Tiền thuế", "Sau thuế"]
            format_dict2 = {col: "{:,.0f}" for col in num_cols2}
            
            styled2 = display_df2.style\
                .apply(style_total, axis=1)\
                .format(format_dict2, na_rep="-")
            
            st.dataframe(styled2, use_container_width=True, height=400)
            
            # Pie chart
            chart_data2 = tax_output_table[tax_output_table["ma"] != "Tổng cộng"].copy()
            if not chart_data2.empty and chart_data2["doanh_so"].sum() > 0:
                fig3 = go.Figure(data=[go.Pie(
                    labels=chart_data2['ma'],
                    values=chart_data2['doanh_so'].abs(),
                    hole=0.45,
                    marker=dict(colors=['#00BCD4', '#2E86C1', '#1B4F72', '#F39C12', '#E74C3C', '#9C27B0', '#4CAF50']),
                    textinfo='label+percent',
                    textfont=dict(size=12, family="Inter"),
                )])
                fig3.update_layout(
                    title="Cơ cấu doanh số bán ra theo mã",
                    template='plotly_dark',
                    height=350,
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(family="Inter"),
                )
                st.plotly_chart(fig3, use_container_width=True)
    
    # ============ TAB 3: ĐỐI CHIẾU CHÉO ============
    with tab3:
        st.markdown(f"#### Đối chiếu chéo 3 cặp dữ liệu — Tháng {period}")
        
        cross_checks = engine.build_cross_check_results()
        
        for check in cross_checks:
            name = check["name"]
            diff = check["difference"]
            
            # Status color
            if diff == 0:
                border_color = "#27AE60"
                status_icon = "✅"
                status_text = "KHỚP"
                bg_grad = "linear-gradient(135deg, #1a2e1a, #1a3d2a)"
            else:
                border_color = "#E74C3C"
                status_icon = "⚠️"
                status_text = "LỆCH"
                bg_grad = "linear-gradient(135deg, #2e1a1a, #3d1a1a)"
            
            st.markdown(f"""
            <div style="
                background: {bg_grad};
                border: 1px solid {border_color};
                border-left: 4px solid {border_color};
                border-radius: 12px;
                padding: 20px;
                margin: 12px 0;
            ">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <h4 style="color: #E0E0E0; margin: 0;">{status_icon} {name}</h4>
                    <span style="
                        background: {'#27AE60' if diff == 0 else '#E74C3C'};
                        color: white; padding: 4px 14px; border-radius: 20px;
                        font-weight: 700; font-size: 0.8rem;
                    ">{status_text}</span>
                </div>
                <div style="margin-top: 12px; display: flex; gap: 30px;">
                    <div>
                        <span style="color: #78909C; font-size: 0.75rem;">{check['source_1']}</span><br>
                        <span style="color: #E0E0E0; font-weight: 600; font-size: 1.1rem;">
                            {check['value_1']:,.0f}
                        </span>
                    </div>
                    <div style="color: #78909C; align-self: center; font-size: 1.2rem;">vs</div>
                    <div>
                        <span style="color: #78909C; font-size: 0.75rem;">{check['source_2']}</span><br>
                        <span style="color: #E0E0E0; font-weight: 600; font-size: 1.1rem;">
                            {check['value_2']:,.0f}
                        </span>
                    </div>
                    <div style="border-left: 1px solid rgba(255,255,255,0.1); padding-left: 20px;">
                        <span style="color: #78909C; font-size: 0.75rem;">Chênh lệch</span><br>
                        <span style="
                            color: {'#27AE60' if diff == 0 else '#E74C3C'};
                            font-weight: 700; font-size: 1.1rem;
                        ">{diff:,.0f}</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Nếu có chênh lệch → Phân tích nguyên nhân
            if diff != 0:
                analysis = engine.analyze_difference(name, diff)
                
                col_cause, col_suggest = st.columns(2)
                
                with col_cause:
                    st.markdown(f"""
                    <div style="
                        background: rgba(30, 42, 58, 0.7);
                        border-radius: 10px;
                        padding: 16px;
                        margin: 0 0 8px 0;
                    ">
                        <p style="color: #F39C12; font-weight: 600; margin: 0 0 6px 0;">
                            🔎 Nguyên nhân
                        </p>
                        <p style="color: #B0BEC5; font-size: 0.85rem; margin: 0; white-space: pre-line;">
                            {analysis['cause']}
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col_suggest:
                    st.markdown(f"""
                    <div style="
                        background: rgba(30, 42, 58, 0.7);
                        border-radius: 10px;
                        padding: 16px;
                        margin: 0 0 8px 0;
                    ">
                        <p style="color: #27AE60; font-weight: 600; margin: 0 0 6px 0;">
                            💡 Gợi ý cách giải quyết
                        </p>
                        <p style="color: #B0BEC5; font-size: 0.85rem; margin: 0; white-space: pre-line;">
                            {analysis['suggestion']}
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Show affected documents
                affected = analysis.get("affected_docs", pd.DataFrame())
                if isinstance(affected, pd.DataFrame) and not affected.empty:
                    with st.expander("📄 Xem chứng từ liên quan"):
                        st.dataframe(affected, use_container_width=True, height=200)
