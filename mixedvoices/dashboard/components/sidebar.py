import streamlit as st

from mixedvoices.dashboard.api.client import APIClient
from mixedvoices.dashboard.api.endpoints import (
    get_project_versions_endpoint,
    get_projects_endpoint,
)


class Sidebar:
    def __init__(self, api_client: APIClient):
        self.api_client = api_client

    def render(self) -> None:
        """Render the sidebar"""
        with st.sidebar:
            st.title("🎙️ MixedVoices")
            self._handle_project_selection()

            st.divider()

            with st.expander("Create New Project"):
                self._handle_project_creation()

    def _handle_project_selection(self) -> None:
        """Handle project and version selection"""
        # Fetch projects
        projects_data = self.api_client.fetch_data(get_projects_endpoint())
        projects = projects_data.get("projects", [])

        # Project selection
        st.session_state.current_project = st.selectbox(
            "Select Project", [""] + projects, key="project_selector"
        )

        # Version selection if project is selected
        if st.session_state.current_project:
            versions_data = self.api_client.fetch_data(
                get_project_versions_endpoint(st.session_state.current_project)
            )
            versions = versions_data.get("versions", [])
            st.session_state.current_version = st.selectbox(
                "Select Version",
                [""] + [v["name"] for v in versions],
                key="version_selector",
            )

    def _handle_project_creation(self) -> None:
        """Handle new project creation"""
        # Initialize states if they don't exist
        if "show_project_success" not in st.session_state:
            st.session_state.show_project_success = False

        # Key for project name input to force re-render when needed
        if "project_input_key" not in st.session_state:
            st.session_state.project_input_key = 0

        # Show success message if needed
        if st.session_state.show_project_success:
            st.success("Project created successfully!")
            st.session_state.show_project_success = False

        # Project creation form
        new_project_name = st.text_input(
            "Project Name",
            key=f"project_name_input_{st.session_state.project_input_key}",
        )

        if st.button("Create Project") and new_project_name:
            response = self.api_client.post_data(
                f"projects?name={new_project_name}", {}
            )
            if response.get("message"):
                # Increment the input key to force a fresh input field
                st.session_state.project_input_key += 1
                st.session_state.show_project_success = True
                st.rerun()
