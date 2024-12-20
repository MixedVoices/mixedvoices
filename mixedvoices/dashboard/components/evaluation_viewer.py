from datetime import datetime, timezone

import pandas as pd
import streamlit as st
from api.client import APIClient

from mixedvoices.dashboard.api.endpoints import get_eval_run_endpoint


class EvaluationViewer:
    def __init__(self, api_client: APIClient, project_id: str, version: str):
        self.api_client = api_client
        self.project_id = project_id
        self.version = version

    def display_evaluations_list(self, eval_runs: list) -> None:
        """Display list of evaluation runs with details"""
        # Header row with refresh button
        header_row = st.columns([8, 1])
        with header_row[0]:
            st.write("## Evaluation Runs")
        with header_row[1]:
            if st.button("Refresh", help="Refresh evaluation runs"):
                st.rerun()

        # Create DataFrame and format dates
        display_df = pd.DataFrame(eval_runs)
        display_df["created_at"] = pd.to_datetime(
            display_df["created_at"], unit="s", utc=True
        )
        display_df["created_at"] = display_df["created_at"].dt.strftime(
            "%-I:%M%p %-d %B %Y"
        )

        # Table header
        header_cols = st.columns([3, 2])
        with header_cols[0]:
            st.markdown("**Evaluation ID**")
        with header_cols[1]:
            st.markdown("**Created At**")
        st.markdown(
            "<hr style='margin: 0; padding: 0; background-color: #333; height: 1px;'>",
            unsafe_allow_html=True,
        )

        # Table rows
        for idx, row in display_df.iterrows():
            cols = st.columns([3, 2])
            with cols[0]:
                if st.button(
                    row["run_id"],
                    key=f"id_btn_{row['run_id']}",
                    help="Click to view details",
                ):
                    self.show_evaluation_dialog(eval_runs[idx])
            with cols[1]:
                st.write(row["created_at"])
            st.markdown(
                "<hr style='margin: 0; padding: 0; background-color: #333; height: 1px;'>",
                unsafe_allow_html=True,
            )

    @st.dialog("Evaluation Details", width="large")
    def show_evaluation_dialog(self, eval_run: dict) -> None:
        """Show evaluation run details in a dialog"""
        # Fetch detailed evaluation data
        eval_details = self.api_client.fetch_data(
            get_eval_run_endpoint(self.project_id, self.version, eval_run["run_id"])
        )

        st.subheader(f"Evaluation ID: {eval_run['run_id']}")

        created_time = datetime.fromtimestamp(
            int(eval_run["created_at"]), tz=timezone.utc
        ).strftime("%-I:%M%p %-d %B %Y")
        st.write("Created:", created_time)

        if eval_details and eval_details.get("agents"):
            for idx, agent in enumerate(eval_details["agents"], 1):
                with st.expander(f"Test {idx}", expanded=False):
                    if agent.get("prompt"):
                        st.text_area(
                            "Evaluation Prompt",
                            agent["prompt"],
                            height=100,
                            key=f"prompt_{eval_run['run_id']}_{idx}",
                            disabled=True,
                        )

                    if agent.get("transcript"):
                        st.text_area(
                            "Transcript",
                            agent["transcript"],
                            height=200,
                            key=f"transcript_{eval_run['run_id']}_{idx}",
                            disabled=True,
                        )

                    if agent.get("scores"):
                        st.write("### Scores")
                        for metric, score_data in agent["scores"].items():
                            score = score_data["score"]
                            # Format score based on type
                            if isinstance(score, (int, float)):
                                formatted_score = f"{score}/10"
                            else:
                                formatted_score = str(
                                    score
                                )  # Handle PASS/FAIL/N/A cases

                            # Create score display with color coding
                            if score == "PASS" or (
                                isinstance(score, (int, float)) and score >= 7
                            ):
                                score_html = f'<span style="color: green">{formatted_score}</span>'
                            elif score == "FAIL" or (
                                isinstance(score, (int, float)) and score < 5
                            ):
                                score_html = (
                                    f'<span style="color: red">{formatted_score}</span>'
                                )
                            elif score == "N/A":
                                score_html = f'<span style="color: gray">{formatted_score}</span>'
                            else:
                                score_html = f'<span style="color: orange">{formatted_score}</span>'

                            st.markdown(
                                f"**{metric}:** {score_html}", unsafe_allow_html=True
                            )
                            st.markdown(
                                f"*{score_data.get('explanation', 'No explanation provided')}*"
                            )
                            st.markdown("---")

                    if agent.get("end"):
                        st.write(f"End Status: {agent['end']}")
        else:
            st.error("Failed to load evaluation details")
