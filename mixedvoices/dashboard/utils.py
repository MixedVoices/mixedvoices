import streamlit as st


def disable_evaluation_details_page():
    """Apply styles to permanently grey out evaluation page"""
    nav_style = """
    <style>
    /* Target evaluation page specifically */
    div[data-testid="stSidebarNav"] > ul > li:nth-child(6) {
        opacity: 0.4;
        cursor: not-allowed;
        pointer-events: none;
    }
    div[data-testid="stSidebarNav"] > ul > li:nth-child(6):hover {
        opacity: 0.4;
    }
    </style>
    """
    st.markdown(nav_style, unsafe_allow_html=True)
