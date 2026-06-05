# -*- coding: utf-8 -*-
"""
Module 2: Kiểm dò & Xác thực (Validation Engine).
Hiển thị kết quả kiểm tra tự động.
"""

import streamlit as st
import pandas as pd
from engine.validator import ValidationEngine


def render_validation_module():
    """Render Module 2: Validation Engine."""
    
    st.markdown("""
    <h1 style="
        background: linear-gradient(135deg, #00BCD4, #2E86C1, #1B4F72);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800; font-size: 1.8rem; margin-bottom: 5px;
    ">🔍 Kiểm Dò & Xác Thực</h1>
    <p style="color: #78909C; font-size: 0.9rem; margin-bottom: 20px;">
        Tự động kiểm tra trạng thái chứng từ, đối chiếu doanh thu, và phân loại thuế suất
    </p>
    """, unsafe_allow_html=True)
    
    data_store = st.session_state.get("data_store", {})
    
    if not data_store:
        st.warning("⚠️ Chưa có dữ liệu. Vui lòng upload file ở **Module 1** trước.")
        return
    
    # Run validation button
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        run_btn = st.button("🚀 Chạy kiểm dò", type="primary", use_container_width=True)
    
    if run_btn or st.session_state.get("validation_results"):
        if run_btn:
            with st.spinner("⏳ Đang kiểm tra dữ liệu..."):
                engine = ValidationEngine(data_store)
                results = engine.run_all_checks()
                st.session_state["validation_results"] = results
        
        results = st.session_state.get("validation_results", {})
        if not results:
            return
        
        summary = results.get("summary", {})
        
        # ============ SUMMARY CARDS ============
        st.markdown("---")
        st.markdown("### 📈 Tổng quan kết quả")
        
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("Tổng kiểm tra", summary.get("total_checks", 0))
        with c2:
            st.metric("✅ Đạt", summary.get("passed", 0))
        with c3:
            st.metric("⚠️ Cảnh báo", summary.get("warnings", 0))
        with c4:
            st.metric("❌ Lỗi", summary.get("errors", 0))
        
        # Overall status
        status = summary.get("overall_status", "pass")
        if status == "pass":
            st.success("🎉 **Tất cả kiểm tra đều PASS!** Dữ liệu hợp lệ, sẵn sàng lên tờ khai.")
        elif status == "warning":
            st.warning("⚠️ **Có cảnh báo cần xem xét.** Kiểm tra chi tiết bên dưới.")
        else:
            st.error("❌ **Phát hiện lỗi nghiêm trọng!** Cần xử lý trước khi lên tờ khai.")
        
        # ============ DETAILED RESULTS ============
        st.markdown("---")
        st.markdown("### 📋 Chi tiết kiểm tra")
        
        for result in results.get("results", []):
            check_name = result.get("check", "")
            check_status = result.get("status", "")
            check_msg = result.get("message", "")
            
            # Status icon
            if check_status == "pass":
                icon = "✅"
                color = "#27AE60"
            elif check_status == "warning":
                icon = "⚠️"
                color = "#F39C12"
            elif check_status == "error":
                icon = "❌"
                color = "#E74C3C"
            else:
                icon = "⏭️"
                color = "#78909C"
            
            with st.expander(f"{icon} {check_name} — {check_msg}", expanded=(check_status in ["error", "warning"])):
                # Details table if available
                details = result.get("details", {})
                if details:
                    detail_df = pd.DataFrame([
                        {"Chỉ tiêu": k, "Giá trị": v}
                        for k, v in details.items()
                    ])
                    st.dataframe(detail_df, use_container_width=True, hide_index=True)
        
        # ============ ERRORS ============
        errors = results.get("errors", [])
        if errors:
            st.markdown("---")
            st.markdown("### 🚨 Chi tiết Lỗi")
            
            for err in errors:
                with st.container():
                    st.markdown(f"""
                    <div style="
                        background: linear-gradient(135deg, #3d1111, #5a1a1a);
                        border: 1px solid #E74C3C;
                        border-radius: 12px;
                        padding: 20px;
                        margin: 10px 0;
                    ">
                        <h4 style="color: #EF5350; margin: 0 0 8px 0;">
                            🔴 {err.get('source', '')}
                        </h4>
                        <p style="color: #FFCDD2; margin: 0 0 8px 0;">
                            {err.get('message', '')}
                        </p>
                        <p style="color: #EF9A9A; font-size: 0.85rem; margin: 0;">
                            {err.get('detail', '')}
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Suggestion
                    suggestion = err.get("suggestion", "")
                    if suggestion:
                        st.info(f"💡 **Gợi ý xử lý:** {suggestion}")
                    
                    # Affected documents
                    affected = err.get("data", pd.DataFrame())
                    if isinstance(affected, pd.DataFrame) and not affected.empty:
                        with st.expander("📄 Xem danh sách chứng từ bị ảnh hưởng"):
                            # Highlight status column
                            def highlight_status(row):
                                status = row.get("trang_thai", "")
                                if status in ["Draft"]:
                                    return ['background-color: #7d5a00'] * len(row)
                                elif status in ["Unpost"]:
                                    return ['background-color: #7a1a1a'] * len(row)
                                elif status in ["Not Reversed"]:
                                    return ['background-color: #4a1a5e'] * len(row)
                                return [''] * len(row)
                            
                            styled = affected.style.apply(highlight_status, axis=1)
                            st.dataframe(styled, use_container_width=True, height=250)
        
        # ============ WARNINGS ============
        warnings = results.get("warnings", [])
        if warnings:
            st.markdown("---")
            st.markdown("### ⚠️ Chi tiết Cảnh báo")
            
            for warn in warnings:
                with st.expander(f"⚠️ {warn.get('source', '')} — {warn.get('message', '')}"):
                    detail = warn.get("detail", "")
                    if detail:
                        st.markdown(f"**Chi tiết:** {detail}")
                    
                    suggestion = warn.get("suggestion", "")
                    if suggestion:
                        st.info(f"💡 **Gợi ý:** {suggestion}")
                    
                    data = warn.get("data", pd.DataFrame())
                    if isinstance(data, pd.DataFrame) and not data.empty:
                        st.dataframe(data, use_container_width=True, height=200)
