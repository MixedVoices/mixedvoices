import streamlit as st
from dashboard.api.client import APIClient
from dashboard.components.sidebar import Sidebar
from dashboard.components.project_manager import ProjectManager
from dashboard.config import DEFAULT_PAGE_CONFIG
import streamlit.components.v1 as components

def hide_pages():
    """Hide all pages except main"""
    # Note: This is using an undocumented API but is currently the only way
    # to dynamically hide pages
    no_sidebar_style = """
        <style>
            div[data-testid="stSidebarNav"] {display: none;}
        </style>
    """
    st.markdown(no_sidebar_style, unsafe_allow_html=True)

def show_pages():
    """Show all pages"""
    show_pages_style = """
        <style>
            div[data-testid="stSidebarNav"] {display: block;}
        </style>
    """
    st.markdown(show_pages_style, unsafe_allow_html=True)

def main():
    """Main application"""
    # Set page config
    st.set_page_config(**DEFAULT_PAGE_CONFIG)
    
    # Initialize API client
    api_client = APIClient()
    
    # Check if we should show other pages
    if not st.session_state.get('current_project') or not st.session_state.get('current_version'):
        hide_pages()
    else:
        show_pages()
    
    # Render sidebar
    sidebar = Sidebar(api_client)
    sidebar.render()
    
    # Main content
    if not st.session_state.get('current_project'):
        st.title("Welcome to MixedVoices")
        st.markdown("""
        ### Getting Started
        1. Select or create a project using the sidebar
        2. Add versions to track changes
        3. Upload recordings to analyze
        """)
        return
    
    # Project view
    if not st.session_state.get('current_version'):
        project_manager = ProjectManager(api_client, st.session_state.current_project)
        project_manager.render()
        return
        
    # If we have both project and version, redirect to flow
    st.switch_page("pages/1_flow.py")

if __name__ == "__main__":
    main()