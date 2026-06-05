# -*- coding: utf-8 -*-
"""
Module 1: Nhập dữ liệu (Data Ingestion)
Upload file PDF/Excel/CSV và tự động parse.
"""

import streamlit as st
import pandas as pd
import os
import time

from config import REQUIRED_FILES, OPTIONAL_FILES, DATA_DIR
from parsers.gcs_parser import parse_gcs
from parsers.gl_parser import parse_gl_tk511
from parsers.ta030_parser import parse_ta030
from parsers.ta035_parser import parse_ta035
from parsers.ta036_parser import parse_ta036
from parsers.nhom_tc_parser import parse_nhom_tc


def render_upload_module():
    """Render Module 1: Upload & Data Ingestion."""
    
    # Check if sample files exist in the parent folder
    sample_files = {
        "gcs": "GCS.pdf",
        "gl_tk511": "GL_0903_TK511.pdf",
        "ta030_tk3331": "TA_030_TK3331.pdf",
        "ta030_tk1331": "TA_030_TK1331.pdf",
        "ta035": "TA_035_TK33311.pdf",
        "ta036": "TA_036_TK13311.pdf",
        "nhom_tc": "NhomTC.pdf"
    }
    
    parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    col_hdr1, col_hdr2 = st.columns([3, 1])
    with col_hdr1:
        st.markdown("""
        <h1 style="
            background: linear-gradient(135deg, #00BCD4, #2E86C1, #1B4F72);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 800; font-size: 1.8rem; margin-bottom: 5px;
        ">📥 Nhập Dữ Liệu Báo Cáo</h1>
        <p style="color: #78909C; font-size: 0.9rem; margin-bottom: 20px;">
            Upload các file báo cáo hàng tháng hoặc sử dụng dữ liệu kiểm thử
        </p>
        """, unsafe_allow_html=True)
    with col_hdr2:
        st.write("") # spacing
        st.write("")
        if st.button("⚡ Tải dữ liệu mẫu T4/2026", help="Tải trực tiếp các file PDF mẫu có sẵn trong thư mục dự án", use_container_width=True):
            try:
                with st.spinner("⏳ Đang tải dữ liệu mẫu..."):
                    loaded_count = 0
                    for key, filename in sample_files.items():
                        filepath = os.path.join(parent_dir, filename)
                        if os.path.exists(filepath):
                            if key == "gcs":
                                result = parse_gcs(filepath)
                            elif key == "gl_tk511":
                                result = parse_gl_tk511(filepath)
                            elif key == "ta030_tk3331":
                                result = parse_ta030(filepath, account_type="output")
                            elif key == "ta030_tk1331":
                                result = parse_ta030(filepath, account_type="input")
                            elif key == "ta035":
                                result = parse_ta035(filepath)
                            elif key == "ta036":
                                result = parse_ta036(filepath)
                            elif key == "nhom_tc":
                                result = parse_nhom_tc(filepath)
                            
                            st.session_state["data_store"][key] = result
                            loaded_count += 1
                    
                    if loaded_count > 0:
                        st.session_state["set_sample_period"] = True
                        st.session_state["period"] = "04/2026"
                        st.session_state["khau_tru_ky_truoc"] = 1500000000
                        st.success(f"✅ Đã tải thành công {loaded_count} file dữ liệu mẫu cho Tháng 04/2026!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Không tìm thấy các file dữ liệu mẫu trong thư mục dự án.")
            except Exception as e:
                st.error(f"❌ Lỗi khi tải dữ liệu mẫu: {str(e)}")
    
    # Initialize data store
    if "data_store" not in st.session_state:
        st.session_state["data_store"] = {}
    
    period = st.session_state.get("period", "")
    
    # ============ REQUIRED FILES ============
    st.markdown("### 📂 File bắt buộc")
    st.markdown(f"*Kỳ báo cáo: **Tháng {period}***")
    
    # Two columns layout for uploads
    col_left, col_right = st.columns(2)
    
    file_keys = list(REQUIRED_FILES.keys())
    
    for idx, (key, info) in enumerate(REQUIRED_FILES.items()):
        col = col_left if idx % 2 == 0 else col_right
        
        with col:
            with st.container():
                st.markdown(f"""
                <div style="
                    background: linear-gradient(135deg, #1e2a3a, #263d55);
                    border: 1px solid rgba(0, 188, 212, 0.15);
                    border-radius: 12px;
                    padding: 16px;
                    margin-bottom: 12px;
                ">
                    <p style="font-weight: 600; color: #E0E0E0; margin: 0 0 4px 0;">
                        {info['label']}
                    </p>
                    <p style="color: #78909C; font-size: 0.75rem; margin: 0;">
                        {info['description']}
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                uploaded = st.file_uploader(
                    f"Upload {info['label']}",
                    type=["pdf", "csv", "xlsx", "xls"],
                    key=f"upload_{key}",
                    label_visibility="collapsed",
                )
                
                if uploaded:
                    _process_file(key, uploaded, info)
    
    # ============ OPTIONAL FILES ============
    st.markdown("---")
    st.markdown("### 📎 File bổ sung (tùy chọn)")
    
    col_opt1, col_opt2 = st.columns(2)
    
    for idx, (key, info) in enumerate(OPTIONAL_FILES.items()):
        col = col_opt1 if idx % 2 == 0 else col_opt2
        
        with col:
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, #1e2a3a, #263d55);
                border: 1px dashed rgba(0, 188, 212, 0.15);
                border-radius: 12px;
                padding: 16px;
                margin-bottom: 8px;
            ">
                <p style="font-weight: 600; color: #B0BEC5; margin: 0 0 4px 0;">
                    {info['label']}
                </p>
                <p style="color: #607D8B; font-size: 0.75rem; margin: 0;">
                    {info['description']}
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            uploaded = st.file_uploader(
                f"Upload {info['label']}",
                type=["pdf", "csv", "xlsx", "xls"],
                key=f"upload_{key}",
                label_visibility="collapsed",
            )
            
            if uploaded:
                _process_file(key, uploaded, info)
    
    # ============ DATA PREVIEW ============
    st.markdown("---")
    _render_data_preview()
    
    # ============ SAVE BUTTON ============
    st.markdown("---")
    data_store = st.session_state.get("data_store", {})
    has_data = any(
        bool(v) and (not isinstance(v, dict) or v.get("data") is not None)
        for v in data_store.values()
    )
    
    if has_data:
        col_save1, col_save2, col_save3 = st.columns([1, 1, 2])
        with col_save1:
            if st.button("💾 Lưu dữ liệu ra Excel", type="primary", use_container_width=True):
                _save_data_to_excel(data_store, period)
        with col_save2:
            if st.button("🗑️ Xóa tất cả dữ liệu", use_container_width=True):
                st.session_state["data_store"] = {}
                st.rerun()


def _process_file(key, uploaded_file, info):
    """Parse file đã upload và lưu vào session state."""
    try:
        with st.spinner(f"⏳ Đang xử lý {info['label']}..."):
            time.sleep(0.3)  # UX feedback
            
            if key == "gcs" or key == "gcs_prev":
                result = parse_gcs(uploaded_file)
            elif key == "gl_tk511":
                result = parse_gl_tk511(uploaded_file)
            elif key == "ta030_tk3331":
                result = parse_ta030(uploaded_file, account_type="output")
            elif key == "ta030_tk1331":
                result = parse_ta030(uploaded_file, account_type="input")
            elif key == "ta035":
                result = parse_ta035(uploaded_file)
            elif key == "ta036":
                result = parse_ta036(uploaded_file)
            elif key == "nhom_tc":
                result = parse_nhom_tc(uploaded_file)
            else:
                result = {}
            
            st.session_state["data_store"][key] = result
            
            # Count records
            data = result.get("data", pd.DataFrame())
            count = len(data) if not isinstance(data, pd.DataFrame) or not data.empty else 0
            
            if count > 0:
                st.success(f"✅ Đã xử lý thành công: **{count}** bản ghi")
            else:
                st.warning("⚠️ File đã được đọc nhưng không tìm thấy dữ liệu. Kiểm tra lại file.")
    
    except Exception as e:
        st.error(f"❌ Lỗi khi xử lý file: {str(e)}")


def _render_data_preview():
    """Hiển thị preview dữ liệu đã parse."""
    data_store = st.session_state.get("data_store", {})
    
    if not data_store:
        st.info("📭 Chưa có dữ liệu. Hãy upload file ở trên để bắt đầu.")
        return
    
    st.markdown("### 👁️ Xem trước dữ liệu")
    
    # Create tabs for each data source
    available_tabs = []
    available_keys = []
    
    tab_labels = {
        "gcs": "📊 GCS",
        "gl_tk511": "📒 TK511",
        "ta030_tk3331": "📗 TK3331",
        "ta030_tk1331": "📕 TK1331",
        "ta035": "📋 TA035",
        "ta036": "📝 TA036",
        "nhom_tc": "🏭 Nhôm TC",
        "gcs_prev": "📊 GCS (T.trước)",
    }
    
    for key, data in data_store.items():
        if data and isinstance(data, dict):
            df = data.get("data", pd.DataFrame())
            if isinstance(df, pd.DataFrame) and not df.empty:
                available_tabs.append(tab_labels.get(key, key))
                available_keys.append(key)
    
    if not available_tabs:
        st.info("📭 Chưa có dữ liệu hợp lệ.")
        return
    
    tabs = st.tabs(available_tabs)
    
    for tab, key in zip(tabs, available_keys):
        with tab:
            data = data_store[key]
            df = data.get("data", pd.DataFrame())
            
            # Summary metrics
            totals = data.get("totals", {})
            if totals:
                metric_cols = st.columns(min(len(totals), 4))
                for i, (metric_key, metric_val) in enumerate(list(totals.items())[:4]):
                    with metric_cols[i % len(metric_cols)]:
                        label = metric_key.replace("_", " ").title()
                        if isinstance(metric_val, (int, float)):
                            st.metric(label, f"{metric_val:,.0f}")
                        else:
                            st.metric(label, str(metric_val))
            
            # Data table
            st.dataframe(
                df.head(50),
                use_container_width=True,
                height=350,
            )
            st.caption(f"Hiển thị {min(50, len(df))}/{len(df)} bản ghi")


def _save_data_to_excel(data_store, period):
    """Lưu dữ liệu ra file Excel."""
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        filepath = os.path.join(DATA_DIR, f"data_{period.replace('/', '_')}.xlsx")
        
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            for key, data in data_store.items():
                if data and isinstance(data, dict):
                    df = data.get("data", pd.DataFrame())
                    if isinstance(df, pd.DataFrame) and not df.empty:
                        sheet_name = key[:31]  # Excel limit
                        df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        st.success(f"✅ Đã lưu dữ liệu vào: `{filepath}`")
    except Exception as e:
        st.error(f"❌ Lỗi khi lưu file: {str(e)}")
