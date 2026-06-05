# -*- coding: utf-8 -*-
"""
⚡ Ứng dụng Kiểm dò Thuế GTGT
Công ty Điện lực Vũng Tàu - EVN

Streamlit Entry Point
"""

import streamlit as st
import os
import sys

# Add app directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.sidebar import render_sidebar
from ui.module1_upload import render_upload_module
from ui.module2_validation import render_validation_module
from ui.module3_dashboard import render_dashboard_module
from ui.module4_export import render_export_module

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="Kiểm dò Thuế GTGT - ĐLVT",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get help": None,
        "Report a bug": None,
        "About": "Ứng dụng Kiểm dò Thuế GTGT - Công ty Điện lực Vũng Tàu © 2026",
    }
)

# ============================================================
# LOAD CUSTOM CSS
# ============================================================
css_path = os.path.join(os.path.dirname(__file__), "styles", "custom.css")
if os.path.exists(css_path):
    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Additional inline styles
st.markdown("""
<style>
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Smooth scrolling */
    html {
        scroll-behavior: smooth;
    }
    
    /* Main content padding */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# INITIALIZE SESSION STATE
# ============================================================
if "data_store" not in st.session_state:
    st.session_state["data_store"] = {}

if "khau_tru_ky_truoc" not in st.session_state:
    st.session_state["khau_tru_ky_truoc"] = 0

if "validation_results" not in st.session_state:
    st.session_state["validation_results"] = None

# ============================================================
# RENDER APP
# ============================================================

# Sidebar returns current module
current_module = render_sidebar()

# Route to correct module
if current_module == "upload":
    render_upload_module()
elif current_module == "validation":
    render_validation_module()
elif current_module == "dashboard":
    render_dashboard_module()
elif current_module == "export":
    render_export_module()
else:
    render_upload_module()
