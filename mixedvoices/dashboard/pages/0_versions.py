import streamlit as st

from mixedvoices.dashboard.api.client import APIClient
from mixedvoices.dashboard.api.endpoints import project_versions_ep
from mixedvoices.dashboard.components.sidebar import Sidebar
from mixedvoices.dashboard.components.version_creator import VersionCreator
from mixedvoices.dashboard.utils import clear_selected_node_path


def project_home_page():
    if "current_project" not in st.session_state:
        st.switch_page("app.py")
        return

    api_client = APIClient()
    clear_selected_node_path()
    sidebar = Sidebar(api_client)
    sidebar.render()

    version_creator = VersionCreator(api_client, st.session_state.current_project)

    st.title("Versions")
    st.info("💡 Use versions to track different iterations of your agent")

    version_creator.render_version_form()

    st.subheader("Versions List")

    # Fetch and display versions
    versions_data = api_client.fetch_data(
        project_versions_ep(st.session_state.current_project)
    )
    versions = versions_data.get("versions", [])

    if not versions:
        st.warning("No versions found for this project")
        return

    for i, version in enumerate(versions):
        with st.expander(
            f"{version['name']} - Recordings: {version['recording_count']}",
            expanded=False,
        ):
            st.write("Prompt:")
            st.text_area(
                "Prompt",
                version["prompt"],
                height=200,
                disabled=True,
                label_visibility="collapsed",
                key=f"prompt_{i}",
            )
            if version.get("metadata"):
                st.write("Metadata:")
                st.json(version["metadata"])


if __name__ == "__main__":
    project_home_page()
