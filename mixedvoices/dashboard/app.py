import streamlit as st

from mixedvoices.dashboard.api.client import APIClient
from mixedvoices.dashboard.components.project_creator import render_project_creator
from mixedvoices.dashboard.components.sidebar import Sidebar
from mixedvoices.dashboard.config import DEFAULT_PAGE_CONFIG
from mixedvoices.dashboard.utils import apply_nav_styles, clear_selected_node_path


def main():
    """Main application"""
    # Set page config
    st.set_page_config(**DEFAULT_PAGE_CONFIG)
    api_client = APIClient()
    clear_selected_node_path()

    # Initialize session states
    st.session_state.current_project = None
    st.session_state.current_version = None
    # Render sidebar
    sidebar = Sidebar(api_client)
    sidebar.render()
    if "show_create_project" not in st.session_state:
        st.session_state.show_create_project = False

    apply_nav_styles()

    # Main content
    if st.session_state.show_create_project:
        render_project_creator(api_client)
    elif not st.session_state.current_project:
        # Welcome section
        st.title("Welcome to MixedVoices Dashboard")

        # Main description
        # st.header("📊 Your Analytics Hub")
        st.markdown("#### View your Voice Agent analytics and evaluations here")

        st.info("💡 Use the sidebar to navigate between projects or create a new one!")

        st.divider()

        # Resources section
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("📚 [Documentation](https://mixedvoices.gitbook.io/docs)")
            st.caption("Comprehensive guides and tutorials")

        with col2:
            st.markdown(
                "⭐ [GitHub Repository](https://github.com/MixedVoices/mixedvoices)"
            )
            st.caption("Leave a star or contribute to the project")

    else:
        st.switch_page("pages/0_versions.py")


if __name__ == "__main__":
    main()
