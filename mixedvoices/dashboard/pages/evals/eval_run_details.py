import streamlit as st

from mixedvoices.dashboard.api.client import APIClient
from mixedvoices.dashboard.components.sidebar import Sidebar
from mixedvoices.dashboard.utils import display_llm_metrics


def eval_run_details_page():
    """Page to display evaluation run details"""
    if (
        "current_project" not in st.session_state
        or "selected_eval_id" not in st.session_state
        or "selected_run_id" not in st.session_state
    ):
        st.switch_page("pages/evals/evals_list.py")
        return

    api_client = APIClient()
    sidebar = Sidebar(api_client)
    sidebar.render()

    st.title(f"{st.session_state.current_project} | Evaluation Run")

    # Add back button
    if st.button("← Back to Evaluation Details"):
        st.switch_page("pages/evals/eval_details.py")

    # Fetch run details
    run_details = api_client.fetch_data(
        f"projects/{st.session_state.current_project}/evals/{st.session_state.selected_eval_id}/runs/{st.session_state.selected_run_id}"
    )

    if not run_details or "agents" not in run_details:
        st.error("Failed to load evaluation run details")
        return

    st.subheader(f"Run ID: {st.session_state.selected_run_id}")
    st.write(f"Version: {run_details['version']}")

    # Display agents
    for idx, agent in enumerate(run_details["agents"], 1):
        with st.expander(f"Test {idx}", expanded=True):
            # Status indicator
            status_col1, status_col2 = st.columns([1, 5])
            with status_col1:
                if agent.get("error"):
                    st.error("Failed")
                elif not agent.get("ended"):
                    if agent.get("started"):
                        st.info("In Progress")
                    else:
                        st.warning("Not Started")
                else:
                    st.success("Completed")

            # Prompt
            if agent.get("prompt"):
                st.markdown("**Prompt:**")
                st.text_area(
                    "Prompt",
                    agent["prompt"],
                    height=100,
                    disabled=True,
                    label_visibility="collapsed",
                )

            # Error message if any
            if agent.get("error"):
                st.error(f"Error: {agent['error']}")
                continue

            # Transcript
            if agent.get("transcript"):
                with st.expander("Transcript", expanded=False):
                    st.text_area(
                        "Complete Transcript",
                        agent["transcript"],
                        height=300,
                        disabled=True,
                        label_visibility="collapsed",
                    )

            # Scores/Metrics
            if agent.get("scores"):
                st.markdown("**Scores:**")
                display_llm_metrics(agent["scores"])
