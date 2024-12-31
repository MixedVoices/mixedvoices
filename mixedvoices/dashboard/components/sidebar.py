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

            if st.session_state.current_project:
                st.divider()
                st.subheader("Navigation")
                self._render_navigation()

            st.divider()

            # Create Project Button
            if st.button("Create New Project", use_container_width=True):
                st.session_state.show_create_project = True

    def _render_project_selection(self):
        # Fetch projects
        projects_data = self.api_client.fetch_data("projects")
        projects = projects_data.get("projects", [])

        # Project selection
        selected_project = st.selectbox(
            "",  # Empty label since we have the subheader
            [""] + projects,
            index=(
                0
                if not st.session_state.current_project
                else projects.index(st.session_state.current_project) + 1
            ),
            label_visibility="collapsed",
        )

        if selected_project != st.session_state.current_project:
            st.session_state.current_project = selected_project
            st.session_state.current_version = None
            # Redirect to project home on selection
            if selected_project:
                st.switch_page("pages/1_project_home.py")
            st.rerun()

    def _render_navigation(self):
        """Render sidebar navigation links"""
        # Home
        if st.button("Home", use_container_width=True, key="nav_home"):
            st.switch_page("pages/1_project_home.py")

        # Analytics group
        st.write("Analytics")
        if st.button("View Call Flows", use_container_width=True):
            st.switch_page("pages/2_view_flow.py")
        if st.button("View Call Details", use_container_width=True):
            st.switch_page("pages/3_view_recordings.py")
        if st.button("Upload Recordings", use_container_width=True):
            st.switch_page("pages/4_upload_recording.py")

        # Evals group
        st.write("Evals")
        if st.button("View Evaluations", use_container_width=True):
            st.switch_page("pages/5_evals_list.py")
        if st.button("View Evaluation Details", use_container_width=True):
            st.switch_page("pages/6_eval_details.py")

        # Project Home and Metrics
        if st.button("project home", use_container_width=True):
            st.switch_page("pages/1_project_home.py")
        if st.button("Metrics", use_container_width=True):
            st.switch_page("pages/9_metrics_page.py")
