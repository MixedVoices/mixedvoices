import streamlit as st
from dashboard.api.client import APIClient
from dashboard.api.endpoints import get_version_recordings_endpoint

class UploadForm:
    def __init__(self, api_client: APIClient, project_id: str, version: str):
        self.api_client = api_client
        self.project_id = project_id
        self.version = version

    def render(self) -> None:
        """Render upload form"""
        st.subheader("Upload Recording")
        uploaded_file = st.file_uploader("Choose an audio file")
        if uploaded_file and st.button("Upload"):
            files = {"file": uploaded_file}
            response = self.api_client.post_data(
                get_version_recordings_endpoint(self.project_id, self.version),
                files=files
            )
            if response:
                st.success("Recording uploaded successfully!")
                st.rerun()