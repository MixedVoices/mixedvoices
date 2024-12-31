import streamlit as st

from mixedvoices.dashboard.api.client import APIClient
from mixedvoices.dashboard.components.sidebar import Sidebar


def project_home_page():
    if "current_project" not in st.session_state:
        st.switch_page("Home.py")
        return

    api_client = APIClient()
    sidebar = Sidebar(api_client)
    sidebar.render()

    st.title(f"Project: {st.session_state.current_project}")

    # Create Version Button
    st.button("Create New Version")

    # Versions Section
    st.header("Versions")

    # Fetch versions
    versions_data = api_client.fetch_data(
        f"projects/{st.session_state.current_project}/versions"
    )
    versions = versions_data.get("versions", [])

    for version in versions:
        with st.expander(
            f"{version['name']} - Recordings: {version['recording_count']}",
            expanded=True,
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
                    height=100,
                    disabled=True,
                    label_visibility="collapsed",
                )
            if version.get("metadata"):
                st.write("Metadata:")
                st.json(version["metadata"])


if __name__ == "__main__":
    project_home_page()
