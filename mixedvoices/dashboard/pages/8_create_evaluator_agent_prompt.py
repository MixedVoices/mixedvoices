import streamlit as st

from mixedvoices.dashboard.api.client import APIClient
from mixedvoices.dashboard.components.sidebar import Sidebar
from mixedvoices.dashboard.utils import clear_selected_node_path


def create_agent_prompt_page():
    if "current_project" not in st.session_state:
        st.switch_page("app.py")
        return

    api_client = APIClient()
    clear_selected_node_path()
    sidebar = Sidebar(api_client)
    sidebar.render()

    if "agent_prompt" not in st.session_state:
        st.session_state.agent_prompt = ""

    if "user_demographic_info" not in st.session_state:
        st.session_state.user_demographic_info = ""

    st.title("Create Evaluator - Step 1")
    st.subheader("Agent Prompt")

    st.session_state.agent_prompt = st.text_area(
        "Enter agent prompt", st.session_state.agent_prompt, height=300
    )

    st.session_state.user_demographic_info = st.text_area(
        "Enter user demographic info (Optional)",
        st.session_state.user_demographic_info,
        height=200
    )

    if st.button("Next"):
        if not st.session_state.agent_prompt.strip():
            st.error("Please enter an agent prompt")
        else:
            st.switch_page("pages/9_create_evaluator_select_metrics.py")


if __name__ == "__main__":
    create_agent_prompt_page()
