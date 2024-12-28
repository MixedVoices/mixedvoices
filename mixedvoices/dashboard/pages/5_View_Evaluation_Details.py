import streamlit as st

from mixedvoices.dashboard.api.client import APIClient
from mixedvoices.dashboard.api.endpoints import get_eval_details_endpoint
from mixedvoices.dashboard.utils import (
    clear_selected_node_path,
    display_llm_metrics,
    display_llm_metrics_preview,
)


@st.dialog("Agent Details", width="large")
def show_agent_details_dialog(agent: dict, agent_number: int) -> None:
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


def evaluation_details_page():
    if (
        "current_project" not in st.session_state
        or "current_version" not in st.session_state
        or "selected_eval_id" not in st.session_state
    ):
        st.switch_page("pages/4_View_Evaluations.py")
        return

    clear_selected_node_path()

    st.title(f"{st.session_state.current_project} | {st.session_state.current_version}")

    # Initialize API client
    api_client = APIClient()

    # Fetch evaluation details
    eval_details = api_client.fetch_data(
        get_eval_details_endpoint(
            st.session_state.current_project,
            st.session_state.current_version,
            st.session_state.selected_eval_id,
        )
    )

    # Back button
    if st.button("← Back to Evaluations"):
        st.session_state.selected_eval_id = None
        st.switch_page("pages/4_View_Evaluations.py")

    st.subheader(f"Eval id: {st.session_state.selected_eval_id}")

    if not eval_details or not eval_details.get("agents"):
        st.error("Failed to load evaluation details")
        return

    # Display agents in a table-like format
    for idx, agent in enumerate(eval_details["agents"], 1):
        with st.expander(f"Test {idx}", expanded=True):
            preview_cols = st.columns([3, 2])

            with preview_cols[0]:
                if agent.get("prompt"):
                    st.markdown("**Prompt:**")
                    st.text_area(
                        "Prompt",
                        agent["prompt"],
                        height=200,
                        disabled=True,
                        label_visibility="collapsed",
                    )

            with preview_cols[1]:
                if agent.get("scores"):
                    st.markdown("**LLM Metrics:**")
                    llm_metrics_dict = agent["scores"]
                    display_llm_metrics_preview(llm_metrics_dict)

            if st.button("View Details", key=f"details_btn_{idx}"):
                show_agent_details_dialog(agent, idx)


if __name__ == "__main__":
    evaluation_details_page()
