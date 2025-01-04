import streamlit as st

from mixedvoices.dashboard.api.client import APIClient
from mixedvoices.dashboard.api.endpoints import (
    step_recordings_ep,
    version_recordings_ep,
)
from mixedvoices.dashboard.components.recording_viewer import RecordingViewer
from mixedvoices.dashboard.components.sidebar import Sidebar
from mixedvoices.dashboard.components.version_selector import render_version_selector
from mixedvoices.dashboard.visualizations.metrics import display_metrics


def view_recordings_page():
    if "current_project" not in st.session_state:
        st.switch_page("app.py")
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

    if st.session_state.get("selected_path"):
        st.info(f"Filtered by path: {st.session_state.selected_path}")

        if st.button("Clear Filter", key="clear_filter"):
            st.session_state.selected_node_id = None
            st.session_state.selected_path = None
            st.rerun()

    if st.session_state.get("selected_node_id"):
        # Fetch recordings for selected node
        recordings = api_client.fetch_data(
            step_recordings_ep(
                st.session_state.current_project,
                st.session_state.current_version,
                st.session_state.selected_node_id,
            )
        )

        if recordings.get("recordings"):
            display_metrics(recordings["recordings"])
            recording_viewer.display_recordings_list(recordings["recordings"])
        else:
            st.warning("No recordings found for the selected path.")

    else:
        # Fetch recordings
        recordings_data = api_client.fetch_data(
            version_recordings_ep(st.session_state.current_project, selected_version)
        )

        if recordings_data.get("recordings"):
            display_metrics(recordings_data["recordings"])
            recording_viewer.display_recordings_list(recordings_data["recordings"])
        else:
            st.warning(
                "No recordings found for this version."
                " Upload recordings using the Upload tab or using Python API."
            )


if __name__ == "__main__":
    view_recordings_page()
