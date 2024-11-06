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
        with st.expander("Create New Version"):
            new_version_name = st.text_input("Version Name")
            metadata = st.text_area("Metadata (JSON)", "{}")
            if st.button("Create Version"):
                if new_version_name:
                    try:
                        metadata_dict = json.loads(metadata)
                        response = self.api_client.post_data(
                            get_project_versions_endpoint(self.project_id),
                            {"name": new_version_name, "metadata": metadata_dict}
                        )
                        if response.get("message"):
                            st.success(response["message"])
                            st.rerun()
                    except json.JSONDecodeError:
                        st.error("Invalid JSON in metadata field")

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
                            st.markdown(f"""
                            #### {version['name']}
                            - Recordings: {version['recording_count']}
                            - Metadata: {version['metadata']}
                            """)