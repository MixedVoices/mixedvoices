import streamlit as st

from mixedvoices.dashboard.api.client import APIClient
from mixedvoices.dashboard.components.sidebar import Sidebar
from mixedvoices.dashboard.components.upload_form import UploadForm
from mixedvoices.dashboard.components.version_selector import render_version_selector
from mixedvoices.dashboard.utils import clear_selected_node_path


def upload_recording_page():
    if "current_project" not in st.session_state:
        st.switch_page("app.py")
        return

    api_client = APIClient()
    clear_selected_node_path()
    sidebar = Sidebar(api_client)
    sidebar.render()

    st.title("Upload Recording")

    # Version selection required
    selected_version = render_version_selector(
        api_client, st.session_state.current_project
    )
    if not selected_version:
        return

    # Reuse the UploadForm component
    upload_form = UploadForm(
        api_client, st.session_state.current_project, selected_version
    )
    upload_form.render()


if __name__ == "__main__":
    upload_recording_page()
