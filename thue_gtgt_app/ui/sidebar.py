# -*- coding: utf-8 -*-
"""
Sidebar - Navigation và cấu hình chung.
"""

import streamlit as st
from datetime import datetime


def render_sidebar():
    """Render sidebar navigation."""
    with st.sidebar:
        # Logo & Title
        st.markdown("""
        <div style="text-align: center; padding: 10px 0 20px 0;">
            <div style="font-size: 2.5rem;">⚡</div>
            <h2 style="
                background: linear-gradient(135deg, #00BCD4, #2E86C1);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                margin: 0; font-size: 1.3rem; font-weight: 800;
                letter-spacing: -0.3px;
            ">KIỂM DÒ THUẾ GTGT</h2>
            <p style="color: #78909C; font-size: 0.75rem; margin-top: 4px;">
                Công ty Điện lực Vũng Tàu
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Kỳ báo cáo
        st.markdown("##### 📅 Kỳ báo cáo")
        
        # Check trigger to set sample period
        if st.session_state.get("set_sample_period"):
            st.session_state["report_month"] = 4
            st.session_state["report_year"] = 2026
            st.session_state["set_sample_period"] = False
            
        # Get default indices
        from datetime import datetime
        default_month = st.session_state.get("report_month", datetime.now().month)
        try:
            month_index = list(range(1, 13)).index(default_month)
        except ValueError:
            month_index = datetime.now().month - 1
            
        current_year = datetime.now().year
        years = list(range(2024, current_year + 2))
        default_year = st.session_state.get("report_year", current_year)
        try:
            year_index = years.index(default_year)
        except ValueError:
            year_index = current_year - 2024

        col1, col2 = st.columns(2)
        with col1:
            month = st.selectbox(
                "Tháng",
                options=list(range(1, 13)),
                index=month_index,
                key="report_month"
            )
        with col2:
            year = st.selectbox(
                "Năm",
                options=years,
                index=year_index,
                key="report_year"
            )
        
        st.session_state["period"] = f"{month:02d}/{year}"
        
        st.markdown("---")
        
        # Navigation
        st.markdown("##### 🧭 Chức năng")
        
        modules = {
            "📥 Nhập dữ liệu": "upload",
            "🔍 Kiểm dò & Xác thực": "validation",
            "📊 Đối chiếu (TAX_VTA)": "dashboard",
            "📋 Tờ khai Thuế GTGT": "export",
        }
        
        selected = st.radio(
            "Chọn module",
            options=list(modules.keys()),
            label_visibility="collapsed",
            key="nav_radio"
        )
        
        st.session_state["current_module"] = modules[selected]
        
        st.markdown("---")
        
        # Thuế GTGT khấu trừ kỳ trước
        st.markdown("##### 💰 Khấu trừ kỳ trước")
        khau_tru = st.number_input(
            "Thuế GTGT còn khấu trừ (VND)",
            min_value=0,
            value=st.session_state.get("khau_tru_ky_truoc", 0),
            step=1000000,
            format="%d",
            key="khau_tru_input",
            help="Nhập số thuế GTGT còn được khấu trừ từ kỳ trước chuyển sang"
        )
        st.session_state["khau_tru_ky_truoc"] = khau_tru
        
        st.markdown("---")
        
        # Data status
        st.markdown("##### 📦 Trạng thái dữ liệu")
        data_store = st.session_state.get("data_store", {})
        
        status_items = [
            ("GCS", "gcs"),
            ("TK511", "gl_tk511"),
            ("TK3331", "ta030_tk3331"),
            ("TK1331", "ta030_tk1331"),
            ("TA035", "ta035"),
            ("TA036", "ta036"),
        ]
        
        for label, key in status_items:
            data = data_store.get(key, {})
            has_data = bool(data) and (
                (isinstance(data, dict) and not data.get("data", None) is None and 
                 (not hasattr(data.get("data"), "empty") or not data["data"].empty))
            )
            icon = "🟢" if has_data else "⚫"
            st.markdown(f"<span style='font-size: 0.85rem;'>{icon} {label}</span>", 
                       unsafe_allow_html=True)
        
        # Footer
        st.markdown("---")
        st.markdown("""
        <div style="text-align: center; padding: 8px 0;">
            <p style="color: #546E7A; font-size: 0.7rem; margin: 0;">
                Phiên bản 1.0.0<br>
                © 2026 Công ty Điện lực Vũng Tàu
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    return st.session_state.get("current_module", "upload")
