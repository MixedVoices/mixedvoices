import streamlit as st

from mixedvoices.dashboard.api.client import APIClient
from mixedvoices.dashboard.api.endpoints import get_eval_run_endpoint


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
        st.markdown("### Scores")

        # Pre-process scores into pairs
        scores_items = list(agent["scores"].items())
        score_pairs = [scores_items[i : i + 2] for i in range(0, len(scores_items), 2)]

        # Create score cards row by row
        for score_pair in score_pairs:
            score_cols = st.columns(2)

            for col_idx, (metric, score_data) in enumerate(score_pair):
                with score_cols[col_idx]:
                    score = score_data["score"]

                    # Format score
                    if isinstance(score, (int, float)):
                        formatted_score = f"{score}/10"
                    else:
                        formatted_score = str(score)

                    # Determine color based on score
                    if score == "PASS" or (
                        isinstance(score, (int, float)) and score >= 7
                    ):
                        color = "green"
                    elif score == "FAIL" or (
                        isinstance(score, (int, float)) and score < 5
                    ):
                        color = "red"
                    elif score == "NA":
                        color = "gray"
                    else:
                        color = "orange"

                    # Create score container with visual separation
                    st.markdown(
                        f"""
                        <div style="background-color: #1E1E1E; border-radius: 5px; padding: 15px; margin: 5px 0;">
                            <div style="border-bottom: 1px solid #333; padding-bottom: 8px; margin-bottom: 8px;">
                                <strong>{metric}:</strong> <span style='color: {color}'>{formatted_score}</span>
                            </div>
                            <div style="color: #AAAAAA; font-size: 0.9em;">Explanation:</div>
                            <div style="padding: 5px 0;">{score_data.get('explanation', 'No explanation provided')}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )


def evaluation_details_page():
    if (
        "current_project" not in st.session_state
        or "current_version" not in st.session_state
        or "selected_eval_id" not in st.session_state
    ):
        st.switch_page("pages/4_View_Evaluations.py")
        return

    st.title(f"{st.session_state.current_project} | {st.session_state.current_version}")

    # Initialize API client
    api_client = APIClient()

    # Fetch evaluation details
    eval_details = api_client.fetch_data(
        get_eval_run_endpoint(
            st.session_state.current_project,
            st.session_state.current_version,
            st.session_state.selected_eval_id,
        )
    )

    # Back button
    if st.button("← Back to Evaluations"):
        st.session_state.selected_eval_id = None
        st.switch_page("pages/4_View_Evaluations.py")

    st.subheader(f"Run id: {st.session_state.selected_eval_id}")

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
                    st.markdown("**Scores:**")
                    score_cols = st.columns(2)
                    for i, (metric, score_data) in enumerate(agent["scores"].items()):
                        with score_cols[i % 2]:
                            score = score_data["score"]
                            if isinstance(score, (int, float)):
                                formatted_score = f"{score}/10"
                            else:
                                formatted_score = str(score)

                            if score == "PASS" or (
                                isinstance(score, (int, float)) and score >= 7
                            ):
                                color = "green"
                            elif score == "FAIL" or (
                                isinstance(score, (int, float)) and score < 5
                            ):
                                color = "red"
                            elif score == "NA":
                                color = "gray"
                            else:
                                color = "orange"

                            st.markdown(
                                f"**{metric}:** <span style='color: {color}'>{formatted_score}</span>",
                                unsafe_allow_html=True,
                            )

            if st.button("View Details", key=f"details_btn_{idx}"):
                show_agent_details_dialog(agent, idx)


if __name__ == "__main__":
    evaluation_details_page()
