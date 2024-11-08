import streamlit as st
import json
from dashboard.api.client import APIClient
from dashboard.api.endpoints import get_project_versions_endpoint

class ProjectManager:
    def __init__(self, api_client: APIClient, project_id: str):
        self.api_client = api_client
        self.project_id = project_id

    def render(self) -> None:
        """Render project management view"""
        st.title(f"Project: {self.project_id}")
        self._render_version_creation()
        self._render_versions_list()

    def _render_version_creation(self) -> None:
        """Render version creation form"""
        # Initialize the expander state
        if "expander_state" not in st.session_state:
            st.session_state.expander_state = True
            
        # Initialize the form fields if they don't exist
        if "version_name" not in st.session_state:
            st.session_state.version_name = ""
        if "version_metadata" not in st.session_state:
            st.session_state.version_metadata = "{}"
        
        # Define callback to handle form submission
        def handle_create_version():
            try:
                metadata_dict = json.loads(st.session_state.version_metadata)
                response = self.api_client.post_data(
                    get_project_versions_endpoint(self.project_id),
                    {"name": st.session_state.version_name, "metadata": metadata_dict}
                )
                if response.get("message"):
                    st.success(response["message"])
                    # Clear the form fields
                    st.session_state.version_name = ""
                    st.session_state.version_metadata = "{}"
                    # Keep expander open
                    st.session_state.expander_state = True
            except json.JSONDecodeError:
                st.error("Invalid JSON in metadata field")

        with st.expander("Create New Version", expanded=st.session_state.expander_state):
            # Create form with key
            with st.form(key="version_creation_form"):
                st.text_input(
                    "Version Name",
                    key="version_name",
                )
                st.text_area(
                    "Metadata (JSON)",
                    key="version_metadata",
                )
                submit_button = st.form_submit_button(
                    "Create Version",
                    on_click=handle_create_version
                )

    def _render_versions_list(self) -> None:
        """Render list of versions"""
        versions_data = self.api_client.fetch_data(
            get_project_versions_endpoint(self.project_id)
        )
        versions = versions_data.get("versions", [])
        
        if versions:
            st.subheader("Versions")
            for i in range(0, len(versions), 3):
                cols = st.columns(3)
                for j, col in enumerate(cols):
                    if i + j < len(versions):
                        version = versions[i + j]
                        with col:
                            st.markdown(f"#### {version['name']}")
                            st.markdown(f"Recordings: {version['recording_count']}")
                            # Format metadata as bullet points
                            st.markdown("Metadata:")
                            for key, value in version['metadata'].items():
                                st.markdown(f"* {key}: {value}")