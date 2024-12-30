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

    st.title(f"{st.session_state.current_project}")
    st.write("Welcome to your project dashboard!")
    # Placeholder for future project overview content
