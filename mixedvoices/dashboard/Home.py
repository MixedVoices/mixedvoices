# Home.py
import streamlit as st

from mixedvoices.dashboard.api.client import APIClient
from mixedvoices.dashboard.components.project_creator import render_project_creator
from mixedvoices.dashboard.components.sidebar import Sidebar
from mixedvoices.dashboard.config import DEFAULT_PAGE_CONFIG


def apply_nav_styles():
    """Apply minimal styles to the navigation"""
    has_project = bool(st.session_state.get("current_project"))

    nav_style = """
        <style>
            [data-testid="stSidebarNav"] {
                display: none;
            }
            section[data-testid="stSidebar"] > div:first-child {
                width: 350px;
            }
            
            section[data-testid="stSidebar"] a:not([href*="Home.py"]) {
                opacity: %s;
                pointer-events: %s;
                position: relative;
            }
            
            section[data-testid="stSidebar"] a:not([href*="Home.py"]):hover::after {
                content: "Select project first";
                position: absolute;
                left: 100%%;
                margin-left: 10px;
                background: rgba(0, 0, 0, 0.8);
                color: white;
                padding: 5px 10px;
                border-radius: 4px;
                font-size: 12px;
                white-space: nowrap;
                z-index: 1000;
                display: %s;
            }
        </style>
    """ % (
        "1" if has_project else "0.4",  # opacity
        "auto" if has_project else "none",  # pointer-events
        "none" if has_project else "block",  # tooltip display
    )
    st.markdown(nav_style, unsafe_allow_html=True)


def main():
    """Main application"""
    # Set page config
    st.set_page_config(**DEFAULT_PAGE_CONFIG)

    api_client = APIClient()

    # Initialize session states
    if "current_project" not in st.session_state:
        st.session_state.current_project = None
    if "current_version" not in st.session_state:
        st.session_state.current_version = None
    if "show_create_project" not in st.session_state:
        st.session_state.show_create_project = False

    apply_nav_styles()

    # Render sidebar
    sidebar = Sidebar(api_client)
    sidebar.render()

    # Main content
    if st.session_state.show_create_project:
        render_project_creator(api_client)
    elif not st.session_state.current_project:
        st.title("Welcome to MixedVoices")
        st.header("Getting Started")
        st.markdown(
            """
            1. Select or create a project using the sidebar
            2. Add versions to track changes
            3. Upload recordings to analyze
            """
        )
    else:
        st.switch_page("pages/1_project_home.py")


if __name__ == "__main__":
    main()
