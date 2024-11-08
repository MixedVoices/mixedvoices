import streamlit as st
from dashboard.api.client import APIClient
from dashboard.api.endpoints import (
    get_version_recordings_endpoint,
    get_step_recordings_endpoint
)
from dashboard.components.recording_viewer import RecordingViewer
from dashboard.visualizations.metrics import display_metrics

def switch_to_flow():
    st.switch_page("pages/1_flow.py")

def recordings_page():
    if 'current_project' not in st.session_state or 'current_version' not in st.session_state:
        st.switch_page("main.py")
        return
        
    st.title(f"Version: {st.session_state.current_version}")
    
    # Initialize API client and components
    api_client = APIClient()
    recording_viewer = RecordingViewer(
        api_client,
        st.session_state.current_project,
        st.session_state.current_version
    )
    
    if st.session_state.get('selected_path'):
        st.info(f"Filtered by path: {st.session_state.selected_path}")
        
        if st.button("Clear Filter", key="clear_filter"):
            st.session_state.selected_node_id = None
            st.session_state.selected_path = None
            switch_to_flow()
    
    if st.session_state.get('selected_node_id'):
        # Fetch recordings for selected node
        recordings = api_client.fetch_data(
            get_step_recordings_endpoint(
                st.session_state.current_project,
                st.session_state.current_version,
                st.session_state.selected_node_id
            )
        )
        
        if recordings.get("recordings"):
            display_metrics(recordings["recordings"])
            recording_viewer.display_recordings_list(recordings["recordings"])
        else:
            st.info("No recordings found for the selected path.")
    else:
        # Display all recordings when no node is selected
        recordings_data = api_client.fetch_data(
            get_version_recordings_endpoint(
                st.session_state.current_project,
                st.session_state.current_version
            )
        )
        
        if recordings_data.get("recordings"):
            display_metrics(recordings_data["recordings"])
            recording_viewer.display_recordings_list(recordings_data["recordings"])
        else:
            st.info("No recordings found for this version. Upload recordings using the Upload tab.")

if __name__ == "__main__":
    recordings_page()