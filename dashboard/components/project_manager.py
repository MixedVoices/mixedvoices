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
        """Render version creation UI"""
        # Initialize states
        if "expander_state" not in st.session_state:
            st.session_state.expander_state = True
        if "version_name" not in st.session_state:
            st.session_state.version_name = ""
        if "metadata_pairs" not in st.session_state:
            st.session_state.metadata_pairs = [{"key": "", "value": ""}]

        with st.expander("Create New Version", expanded=st.session_state.expander_state):
            # Version name input
            version_name = st.text_input(
                "Version Name",
                value=st.session_state.version_name
            )
            
            st.subheader("Metadata")
            
            # Handle metadata pairs
            to_remove = None
            for i, pair in enumerate(st.session_state.metadata_pairs):
                col1, col2, col3 = st.columns([2, 2, 1])
                
                with col1:
                    key = st.text_input(
                        "Key",
                        value=pair["key"],
                        key=f"key_{i}",
                        label_visibility="collapsed",
                        placeholder="Enter key"
                    )
                    st.session_state.metadata_pairs[i]["key"] = key
                
                with col2:
                    value = st.text_input(
                        "Value",
                        value=pair["value"],
                        key=f"value_{i}",
                        label_visibility="collapsed",
                        placeholder="Enter value"
                    )
                    st.session_state.metadata_pairs[i]["value"] = value
                
                with col3:
                    if i > 0:  # Don't show remove button for first pair
                        if st.button("✕", key=f"remove_{i}"):
                            to_remove = i
            
            # Handle remove after the loop to avoid modifying list while iterating
            if to_remove is not None:
                st.session_state.metadata_pairs.pop(to_remove)
                st.rerun()
            
            # Add new metadata field button
            if st.button("Add Metadata Field"):
                st.session_state.metadata_pairs.append({"key": "", "value": ""})
                st.rerun()
            
            # Create version button
            if st.button("Create Version"):
                if version_name:
                    # Convert metadata pairs to dictionary
                    metadata_dict = {
                        pair["key"]: pair["value"] 
                        for pair in st.session_state.metadata_pairs 
                        if pair["key"].strip()  # Only include pairs with non-empty keys
                    }
                    
                    response = self.api_client.post_data(
                        get_project_versions_endpoint(self.project_id),
                        {"name": version_name, "metadata": metadata_dict}
                    )
                    
                    if response.get("message"):
                        st.success(response["message"])
                        # Clear the fields
                        st.session_state.version_name = ""
                        st.session_state.metadata_pairs = [{"key": "", "value": ""}]
                        # Keep expander open
                        st.session_state.expander_state = True
                        st.rerun()
                else:
                    st.error("Please enter a version name")

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