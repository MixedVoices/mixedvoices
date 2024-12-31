import streamlit as st

from mixedvoices.dashboard.api.client import APIClient
from mixedvoices.dashboard.components.recording_viewer import RecordingViewer
from mixedvoices.dashboard.components.sidebar import Sidebar
from mixedvoices.dashboard.components.version_selector import render_version_selector
from mixedvoices.dashboard.visualizations.metrics import display_metrics


def view_recordings_page():
    if "current_project" not in st.session_state:
        st.switch_page("Home.py")
        return

    api_client = APIClient()
    sidebar = Sidebar(api_client)
    sidebar.render()

    st.title("Call Details")

    # Version selection required
    selected_version = render_version_selector(
        api_client, st.session_state.current_project
    )
    if not selected_version:
        return

    # Reuse the RecordingViewer component
    recording_viewer = RecordingViewer(
        api_client, st.session_state.current_project, selected_version
    )

    # Fetch recordings
    recordings_data = api_client.fetch_data(
        f"projects/{st.session_state.current_project}/versions/{selected_version}/recordings"
    )

    if recordings_data.get("recordings"):
        display_metrics(recordings_data["recordings"])
        recording_viewer.display_recordings_list(recordings_data["recordings"])
    else:
        st.info("No recordings found. Upload recordings using the Upload tab.")


if __name__ == "__main__":
    view_recordings_page()
