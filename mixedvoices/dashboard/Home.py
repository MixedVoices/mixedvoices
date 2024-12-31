# Home.py
import streamlit as st

from mixedvoices.dashboard.api.client import APIClient
from mixedvoices.dashboard.components.project_creator import render_project_creator
from mixedvoices.dashboard.components.sidebar import Sidebar
from mixedvoices.dashboard.config import DEFAULT_PAGE_CONFIG


def main():
    """Main application"""
    # Set page config
    st.set_page_config(**DEFAULT_PAGE_CONFIG)

    pages = {
        "Dashboard": [
            st.Page("Home.py", title="MixedVoices Home"),
            st.Page("pages/1_project_home.py", title="Project Home"),
            st.Page("pages/9_metrics_page.py", title="Metrics"),
        ],
        "Analytics": [
            st.Page("pages/2_view_flow.py", title="View Call Flows"),
            st.Page("pages/3_view_recordings.py", title="View Call Details"),
            st.Page("pages/4_upload_recording.py", title="Upload Recordings"),
        ],
        "Evals": [
            st.Page("pages/5_evals_list.py", title="View Evaluations"),
            st.Page("pages/6_eval_details.py", title="View Evaluation Details"),
            st.Page("pages/7_eval_run_details.py", title="View Evaluation Run"),
            st.Page("pages/8_create_evaluator.py", title="Create Evaluation"),
        ],
    }

    st.navigation(pages)

    api_client = APIClient()

    # Initialize session states
    if "current_project" not in st.session_state:
        st.session_state.current_project = None
    if "current_version" not in st.session_state:
        st.session_state.current_version = None
    if "show_create_project" not in st.session_state:
        st.session_state.show_create_project = False

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
