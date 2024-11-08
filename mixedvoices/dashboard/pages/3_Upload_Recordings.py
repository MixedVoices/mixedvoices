import streamlit as st

from mixedvoices.dashboard.api.client import APIClient
from mixedvoices.dashboard.components.upload_form import UploadForm


def upload_page():
    if (
        "current_project" not in st.session_state
        or "current_version" not in st.session_state
    ):
        st.switch_page("Home.py")
        return

    st.title(f"{st.session_state.current_project} | {st.session_state.current_version}")

    # Initialize API client
    api_client = APIClient()

    upload_form = UploadForm(
        api_client, st.session_state.current_project, st.session_state.current_version
    )
    upload_form.render()


if __name__ == "__main__":
    upload_page()
