# pages/7_eval_run_details.py

import streamlit as st

from mixedvoices.dashboard.api.client import APIClient
from mixedvoices.dashboard.api.endpoints import eval_run_details_ep
from mixedvoices.dashboard.components.sidebar import Sidebar
from mixedvoices.dashboard.utils import (
    clear_selected_node_path,
    display_llm_metrics,
    display_llm_metrics_preview,
)


@st.dialog("Agent Details", width="large")
def show_agent_details_dialog(agent: dict, agent_number: int) -> None:
    """Dialog to show detailed agent information"""
    st.subheader(f"Agent {agent_number} Details")

    if agent.get("error"):
        st.markdown("**Status:** Failed")
        st.markdown(f"{agent['error']}")
    if agent.get("ended") is False:
        status = "In Progress" if agent.get("started") else "Not Started"
        st.markdown(f"**Status:** {status}")
    if agent.get("transcript"):
        st.markdown("### Transcript")
        st.text_area(
            "Complete Transcript",
            agent["transcript"],
            height=300,
            disabled=True,
        )
    if agent.get("scores"):
        st.markdown("### LLM Metrics")
        display_llm_metrics(agent["scores"])


def eval_run_details_page():
    """Page to display evaluation run details"""
    if (
        "current_project" not in st.session_state
        or "selected_eval_id" not in st.session_state
        or "selected_run_id" not in st.session_state
    ):
        st.switch_page("pages/5_evals_list.py")
        return

    api_client = APIClient()
    clear_selected_node_path()
    sidebar = Sidebar(api_client)
    sidebar.render()

    # Fetch run details
    run_details = api_client.fetch_data(
        eval_run_details_ep(
            st.session_state.current_project,
            st.session_state.selected_eval_id,
            st.session_state.selected_run_id,
        )
    )

    version = run_details.get("version", "N/A")
    st.title(f"Evaluator Run for version: {version}")

    st.markdown(
        f"#### Eval ID: {st.session_state.selected_eval_id} | Run ID: {st.session_state.selected_run_id}"
    )

    # Back button
    if st.button("Back to Evaluator Details", icon=":material/arrow_back:"):
        st.session_state.selected_run_id = None
        st.switch_page("pages/6_eval_details.py")

    if not run_details or not run_details.get("results"):
        st.error("Failed to load evaluation run details")
        return

    # Display agents in a table-like format
    for idx, agent in enumerate(run_details["results"], 1):
        with st.expander(f"Test {idx}", expanded=True):
            preview_cols = st.columns([3, 2, 2])

            with preview_cols[0]:
                if agent.get("test_case"):
                    st.markdown("**Prompt**")
                    st.text_area(
                        "Test Case",
                        agent["test_case"],
                        height=200,
                        disabled=True,
                        label_visibility="collapsed",
                        key=f"test_case_{idx}",
                    )

            with preview_cols[1]:
                is_successful = agent.get("is_successful")
                success_explanation = agent.get("success_explanation")
                st.markdown("**Success**")
                if is_successful is None:
                    st.write("N/A")
                    if success_explanation:
                        st.markdown("**Explanation:**")
                        st.write(success_explanation)
                else:
                    st.write("✅" if is_successful else "❌")

            with preview_cols[2]:
                if agent.get("scores"):
                    st.markdown("**LLM Metrics**")
                    llm_metrics_dict = agent["scores"]
                    display_llm_metrics_preview(llm_metrics_dict)

            if st.button("View Details", key=f"details_btn_{idx}"):
                show_agent_details_dialog(agent, idx)


if __name__ == "__main__":
    eval_run_details_page()
