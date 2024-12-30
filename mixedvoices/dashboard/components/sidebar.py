import streamlit as st


class Sidebar:
    def __init__(self, api_client):
        self.api_client = api_client
        if "current_project" not in st.session_state:
            st.session_state.current_project = None
        if "current_version" not in st.session_state:
            st.session_state.current_version = None

    def render(self):
        with st.sidebar:
            st.title("🎙️ MixedVoices")

            # Project Selection
            self._render_project_selection()

            if st.session_state.current_project:
                self._render_navigation()

            st.divider()

            # Create Project Button
            if st.button("Create New Project"):
                st.session_state.show_create_project = True

    def _render_project_selection(self):
        # Fetch projects
        projects_data = self.api_client.fetch_data("projects")
        projects = projects_data.get("projects", [])

        # Project selection
        selected_project = st.selectbox(
            "Select Project",
            [""] + projects,
            index=(
                0
                if not st.session_state.current_project
                else projects.index(st.session_state.current_project) + 1
            ),
        )

        if selected_project != st.session_state.current_project:
            st.session_state.current_project = selected_project
            st.session_state.current_version = None
            st.rerun()

    def _render_navigation(self):
        st.subheader("Navigation")

        # Project Home
        if st.button("Project Home", use_container_width=True):
            st.switch_page("pages/project_home.py")

        # Analytics Section
        st.subheader("Analytics")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("View Recordings"):
                st.switch_page("pages/analytics/view_recordings.py")
        with col2:
            if st.button("View Flow"):
                st.switch_page("pages/analytics/view_flow.py")
        with col3:
            if st.button("Upload"):
                st.switch_page("pages/analytics/upload_recording.py")

        # Evals Section
        st.subheader("Evals")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Evals List"):
                st.switch_page("pages/evals/evals_list.py")
        with col2:
            if st.button("Create Eval"):
                st.switch_page("pages/evals/create_evaluator.py")

        # Metrics Section
        st.subheader("Metrics")
        if st.button("View Metrics", use_container_width=True):
            st.switch_page("pages/metrics/metrics_page.py")
