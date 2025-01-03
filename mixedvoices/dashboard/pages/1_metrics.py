import streamlit as st

from mixedvoices.dashboard.api.client import APIClient
from mixedvoices.dashboard.components.metrics_manager import MetricsManager
from mixedvoices.dashboard.components.sidebar import Sidebar
from mixedvoices.dashboard.utils import clear_selected_node_path


def metrics_page():
    if "current_project" not in st.session_state:
        st.switch_page("app.py")
        return

    api_client = APIClient()
    clear_selected_node_path()
    sidebar = Sidebar(api_client)
    sidebar.render()

    st.title("Metrics")
    st.info("💡 Metrics are tracked for every call added and for evaluations.")

    metrics_manager = MetricsManager(api_client, st.session_state.current_project)
    metrics_manager.render(selection_mode=False, creation_mode=True)


if __name__ == "__main__":
    metrics_page()
