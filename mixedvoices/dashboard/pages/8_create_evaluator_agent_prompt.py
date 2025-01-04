import streamlit as st

from mixedvoices.dashboard.api.client import APIClient
from mixedvoices.dashboard.api.endpoints import version_ep
from mixedvoices.dashboard.components.sidebar import Sidebar
from mixedvoices.dashboard.components.version_selector import render_version_selector
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
    st.info(
        "💡 Both of these fields are used to auto generate test cases. Not used for evaluation"
    )

    st.subheader("Agent Prompt")
    # Create tabs for prompt selection
    selected_version = render_version_selector(
        api_client, st.session_state.current_project, optional=False
    )
    if selected_version:
        version_data = api_client.fetch_data(
            version_ep(st.session_state.current_project, selected_version)
        )
        st.session_state.agent_prompt = version_data.get("prompt", "")
    else:
        st.session_state.agent_prompt = ""
    st.text_area(
        "Version Prompt (Read-only)",
        value=st.session_state.agent_prompt,
        height=300,
        disabled=True,
        label_visibility="collapsed",
    )

    st.subheader("User Demographic (Optional)")
    st.info("💡 If provided, all test cases created will belong to this demographic")
    st.session_state.user_demographic_info = st.text_area(
        "Enter user demographic info (Optional)",
        st.session_state.user_demographic_info,
        height=200,
        label_visibility="collapsed",
    )

    if st.button("Next"):
        if not st.session_state.agent_prompt.strip():
            st.error("Please enter an agent prompt")
        else:
            st.switch_page("pages/9_create_evaluator_select_metrics.py")


if __name__ == "__main__":
    create_agent_prompt_page()
