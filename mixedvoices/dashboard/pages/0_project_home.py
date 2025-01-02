import streamlit as st

from mixedvoices.dashboard.api.client import APIClient
from mixedvoices.dashboard.components.sidebar import Sidebar
from mixedvoices.dashboard.components.version_creator import VersionCreator


def project_home_page():
    if "current_project" not in st.session_state:
        st.switch_page("app.py")
        return

    api_client = APIClient()
    sidebar = Sidebar(api_client)
    sidebar.render()

    version_manager = VersionCreator(api_client, st.session_state.current_project)

    st.title(f"Project Home: {st.session_state.current_project}")

    # Versions Section
    st.header("Versions")

    if not st.session_state.show_version_creator:
        if st.button("Create New Version"):
            st.session_state.show_version_creator = True
            st.rerun()

    if st.session_state.show_version_creator:
        version_manager.render_version_form()

    # Fetch and display versions
    versions_data = api_client.fetch_data(
        f"projects/{st.session_state.current_project}/versions"
    )
    versions = versions_data.get("versions", [])

    if not versions and not st.session_state.show_version_creator:
        st.info("No versions found for this project")
        return

    for version in versions:
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
            )
            if version.get("success_criteria"):
                st.write("Success Criteria:")
                st.text_area(
                    "Success Criteria",
                    version["success_criteria"],
                    height=200,
                    disabled=True,
                    label_visibility="collapsed",
                )
            if version.get("metadata"):
                st.write("Metadata:")
                st.json(version["metadata"])


if __name__ == "__main__":
    project_home_page()
