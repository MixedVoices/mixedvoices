import streamlit as st

from mixedvoices.dashboard.api.client import APIClient
from mixedvoices.dashboard.components.sidebar import Sidebar
from mixedvoices.dashboard.components.success_criteria_manager import (
    SuccessCriteriaManager,
)
from mixedvoices.dashboard.utils import clear_selected_node_path


def success_criteria_page():
    if "current_project" not in st.session_state:
        st.switch_page("app.py")
        return

    api_client = APIClient()
    clear_selected_node_path()
    sidebar = Sidebar(api_client)
    sidebar.render()

    st.title("Success Criteria")
    st.info(
        "💡 Success criteria, if set is automatically calculated for each call added and for evaluations."
    )

    project_id = st.session_state.current_project
    success_criteria_manager = SuccessCriteriaManager(api_client, project_id)
    success_criteria_manager.render()


if __name__ == "__main__":
    success_criteria_page()
