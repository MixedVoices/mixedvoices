import streamlit as st

from mixedvoices.dashboard.api.endpoints import projects_ep
from mixedvoices.dashboard.utils import clear_session_state


class Sidebar:
    def __init__(self, api_client):
        self.api_client = api_client
        if "current_project" not in st.session_state:
            st.session_state.current_project = None

    def render(self):
        with st.sidebar:
            # Logo and Title
            st.page_link("app.py", label="MixedVoices Home", icon=":material/home:")
            self._render_project_selection()

            # Create Project Button
            if st.button(
                "Create New Project", use_container_width=True, icon=":material/add:"
            ):
                st.session_state.show_create_project = True
                st.switch_page("app.py")

            st.divider()

            st.page_link("pages/0_versions.py", label="Versions")
            st.page_link("pages/1_metrics.py", label="Metrics")
            st.page_link("pages/1_success_criteria.py", label="Success Criteria")

            st.markdown("### Analytics")
            st.page_link("pages/3_view_recordings.py", label="View Call Details")
            st.page_link("pages/2_view_flow.py", label="View Call Flows")
            st.page_link("pages/4_upload_recording.py", label="Upload Calls")

            st.markdown("### Evaluations")
            st.page_link("pages/5_evals_list.py", label="View Evaluators")
            st.page_link(
                "pages/8_create_evaluator_agent_prompt.py", label="Create Evaluator"
            )

    def _render_project_selection(self):
        # Fetch projects
        projects_data = self.api_client.fetch_data(projects_ep())
        projects = projects_data.get("projects", [])

        # Project selection
        selected_project = st.selectbox(
            "selected project",
            [""] + projects,
            index=(
                None
                if not st.session_state.current_project
                else projects.index(st.session_state.current_project) + 1
            ),
            label_visibility="hidden",
            placeholder="Select a project",
        )

        if selected_project != st.session_state.current_project:
            clear_session_state()
            st.session_state.current_project = selected_project
            st.session_state.current_version = None
            if selected_project:
                st.switch_page("pages/0_versions.py")
            else:
                st.switch_page("app.py")
            st.rerun()
