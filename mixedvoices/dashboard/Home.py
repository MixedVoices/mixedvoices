import streamlit as st  # noqa: N999

from mixedvoices.dashboard.api.client import APIClient
from mixedvoices.dashboard.components.project_manager import ProjectManager
from mixedvoices.dashboard.components.sidebar import Sidebar
from mixedvoices.dashboard.config import DEFAULT_PAGE_CONFIG


def apply_nav_styles():
    """Apply navigation styles based on project and version selection"""
    # On home page, always grey out other pages
    if st.session_state.get("current_page") == "home":
        has_project = False
        has_version = False
    else:
        has_project = bool(st.session_state.get("current_project"))
        has_version = bool(st.session_state.get("current_version"))

    nav_style = """
        <style>
            /* Set sidebar width */
            section[data-testid="stSidebar"] > div:first-child {
                width: 350px;
            }

            /* Hide hamburger menu */
            button[kind="header"] {
                display: none;
            }

            /* Style navigation items */
            div[data-testid="stSidebarNav"] > ul {
                padding-top: 2rem;
            }

            div[data-testid="stSidebarNav"] > ul > li:first-child {
                opacity: 1 !important;
                cursor: pointer !important;
            }

            div[data-testid="stSidebarNav"] > ul > li:not(:first-child) {
                opacity: %s;
                cursor: %s;
                pointer-events: %s;
            }

            div[data-testid="stSidebarNav"] > ul > li:not(:first-child):hover {
                opacity: %s;
            }

            /* Add disabled message on hover */
            div[data-testid="stSidebarNav"] > ul > li:not(:first-child)::after {
                content: "%s";
                position: absolute;
                left: 100%%;
                margin-left: 10px;
                background: rgba(0, 0, 0, 0.8);
                padding: 5px 10px;
                border-radius: 4px;
                font-size: 12px;
                white-space: nowrap;
                display: none;
            }

            div[data-testid="stSidebarNav"] > ul > li:not(:first-child):hover::after {
                display: %s;
            }
        </style>
    """ % (
        "1" if has_project and has_version else "0.4",  # opacity
        "pointer" if has_project and has_version else "not-allowed",  # cursor
        "auto" if has_project and has_version else "none",  # pointer-events
        "1" if has_project and has_version else "0.4",  # hover opacity
        (
            "Select project and version first"
            if not has_project
            else "" if has_version else "Select version first"
        ),  # tooltip text
        "none" if has_project and has_version else "block",  # tooltip display
    )
    st.markdown(nav_style, unsafe_allow_html=True)


def main():
    """Main application"""
    # Set page config
    st.set_page_config(**DEFAULT_PAGE_CONFIG)

    # Set current page to home
    st.session_state.current_page = "home"

    # Initialize API client
    api_client = APIClient()

    # Apply navigation styles
    apply_nav_styles()

    # Render sidebar
    sidebar = Sidebar(api_client)
    sidebar.render()

    # Main content
    if not st.session_state.get("current_project"):
        st.title("Welcome to MixedVoices")
        st.markdown(
            """
        ### Getting Started
        1. Select or create a project using the sidebar
        2. Add versions to track changes
        3. Upload recordings to analyze
        """
        )
        return

    # Project view
    if not st.session_state.get("current_version"):
        project_manager = ProjectManager(api_client, st.session_state.current_project)
        project_manager.render()
        return

    # If we have both project and version, redirect to flow
    st.switch_page("pages/1_View_Flowchart.py")


if __name__ == "__main__":
    main()
