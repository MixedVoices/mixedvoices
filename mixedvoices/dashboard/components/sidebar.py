import streamlit as st


class Sidebar:
    def __init__(self, api_client):
        self.api_client = api_client
        if "current_project" not in st.session_state:
            st.session_state.current_project = None

    def render(self):
        with st.sidebar:
            # Logo and Title
            st.title("🎙️ MixedVoices")

            # Project Selection
            st.subheader("Select Project")
            self._render_project_selection()

            # Create Project Button
            if st.button("Create New Project", use_container_width=True):
                st.session_state.show_create_project = True

            st.divider()

            # Navigation sections
            st.markdown("### Dashboard")
            st.page_link("Home.py", label="MixedVoices Home")
            st.page_link("pages/1_project_home.py", label="Project Home")
            st.page_link("pages/9_metrics_page.py", label="Metrics")

            st.markdown("### Analytics")
            st.page_link("pages/2_view_flow.py", label="View Call Flows")
            st.page_link("pages/3_view_recordings.py", label="View Call Details")
            st.page_link("pages/4_upload_recording.py", label="Upload Recordings")

            st.markdown("### Evals")
            st.page_link("pages/5_evals_list.py", label="View Evaluations")
            st.page_link("pages/6_eval_details.py", label="View Evaluation Details")
            st.page_link("pages/7_eval_run_details.py", label="View Evaluation Run")
            st.page_link("pages/8_create_evaluator.py", label="Create Evaluation")

            st.divider()

    def _render_project_selection(self):
        # Fetch projects
        projects_data = self.api_client.fetch_data("projects")
        projects = projects_data.get("projects", [])

        # Project selection
        selected_project = st.selectbox(
            "selected project",
            [""] + projects,
            index=(
                0
                if not st.session_state.current_project
                else projects.index(st.session_state.current_project) + 1
            ),
            label_visibility="hidden",
        )

        if selected_project != st.session_state.current_project:
            st.session_state.current_project = selected_project
            st.session_state.current_version = None
            # Redirect to project home on selection
            if selected_project:
                st.switch_page("pages/1_project_home.py")
            st.rerun()
