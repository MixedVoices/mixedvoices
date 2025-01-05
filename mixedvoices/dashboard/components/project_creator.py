import streamlit as st

from mixedvoices.dashboard.api.endpoints import projects_ep
from mixedvoices.dashboard.components.metrics_manager import MetricsManager


def render_project_creator(api_client):
    """Render project creation form using metrics manager"""
    if st.button("Back", icon=":material/arrow_back:"):
        st.session_state.show_create_project = False
        st.rerun()
    st.header("Create New Project")

    st.markdown("### Project Name")
    project_id = st.text_input("Project Name", label_visibility="collapsed")

    st.divider()

    st.markdown(
        "### Success Criteria",
        help="This will be used to automatically determine if a call is successful or not.",
    )
    success_criteria = st.text_area("Enter success criteria", height=200)
    st.divider()

    st.markdown(
        "### Select Metrics",
        help="These will be analyzed for all calls added. Can be added/updated later if needed.",
    )

    # Use metrics manager for metric selection
    metrics_manager = MetricsManager(api_client)
    selected_metrics = metrics_manager.render(selection_mode=True, creation_mode=True)

    if st.button("Create Project"):
        if project_id:
            response = api_client.post_data(
                projects_ep(),
                json={"metrics": selected_metrics},
                params={"name": project_id, "success_criteria": success_criteria},
            )
            if response.get("message"):
                st.success("Project created successfully!")
                st.session_state.show_create_project = False
                st.session_state.current_project = response.get("project_id")
                st.switch_page("pages/0_versions.py")
                st.rerun()
        else:
            st.error("Please provide a project name")
