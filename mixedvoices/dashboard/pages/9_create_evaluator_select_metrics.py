import streamlit as st

from mixedvoices.dashboard.api.client import APIClient
from mixedvoices.dashboard.components.metrics_manager import MetricsManager
from mixedvoices.dashboard.components.sidebar import Sidebar
from mixedvoices.dashboard.utils import clear_selected_node_path


def select_metrics_page():
    if "current_project" not in st.session_state:
        st.switch_page("app.py")
        return

    if "agent_prompt" not in st.session_state:
        st.switch_page("pages/8_create_evaluator_agent_prompt.py")
        return

    api_client = APIClient()
    clear_selected_node_path()
    sidebar = Sidebar(api_client)
    sidebar.render()

    st.title("Create Evaluator - Step 2")
    st.subheader("Select Metrics")

    st.info("💡 Choose metrics to evaluate agent on. You can only choose from project metrics. Switch to Metrics page to add more.")

    if st.button("Back to Agent Prompt", icon=":material/arrow_back:"):
        st.switch_page("pages/8_create_evaluator_agent_prompt.py")

    metrics_manager = MetricsManager(api_client, st.session_state.current_project)
    selected_metrics = metrics_manager.render(selection_mode=True, creation_mode=False)

    if st.button("Next"):
        if not selected_metrics:
            st.error("Please select at least one metric")
        else:
            st.session_state.selected_metrics = selected_metrics
            st.switch_page("pages/10_create_evaluator_create_prompts.py")


if __name__ == "__main__":
    select_metrics_page()
