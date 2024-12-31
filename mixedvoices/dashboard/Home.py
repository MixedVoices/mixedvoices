# Home.py
import streamlit as st

from mixedvoices.dashboard.api.client import APIClient
from mixedvoices.dashboard.components.project_creator import render_project_creator
from mixedvoices.dashboard.components.sidebar import Sidebar
from mixedvoices.dashboard.config import DEFAULT_PAGE_CONFIG
from mixedvoices.dashboard.utils import apply_nav_styles


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
