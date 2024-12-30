import streamlit as st

from mixedvoices.dashboard.components.metrics_manager import MetricsManager


def render_project_creator(api_client):
    """Render project creation form using metrics manager"""
    st.subheader("Create New Project")

    project_name = st.text_input("Project Name")

    # Use metrics manager for metric selection
    metrics_manager = MetricsManager(api_client)
    selected_metrics = metrics_manager.render(selection_mode=True)

    if st.button("Create Project"):
        if project_name and selected_metrics:
            response = api_client.post_data(
                "projects", {"name": project_name, "metrics": selected_metrics}
            )
            if response.get("message"):
                st.success("Project created successfully!")
                st.session_state.show_create_project = False
                st.rerun()
        else:
            st.error("Please provide project name and select at least one metric")
