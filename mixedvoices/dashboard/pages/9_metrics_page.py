import streamlit as st

from mixedvoices.dashboard.api.client import APIClient
from mixedvoices.dashboard.components.metrics_manager import MetricsManager
from mixedvoices.dashboard.components.sidebar import Sidebar


def metrics_page():
    if "current_project" not in st.session_state:
        st.switch_page("Home.py")
        return

    api_client = APIClient()
    sidebar = Sidebar(api_client)
    sidebar.render()

    st.title("Metrics")

    metrics_manager = MetricsManager(api_client, st.session_state.current_project)
    metrics_manager.render()


if __name__ == "__main__":
    metrics_page()
