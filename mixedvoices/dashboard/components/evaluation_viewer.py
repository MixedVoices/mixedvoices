import pandas as pd
import streamlit as st
from api.client import APIClient


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
        for _, row in display_df.iterrows():
            cols = st.columns([3, 2])
            with cols[0]:
                if st.button(
                    row["run_id"],
                    key=f"id_btn_{row['run_id']}",
                    help="Click to view details",
                ):
                    # Store the selected evaluation ID in session state
                    st.session_state.selected_eval_id = row["run_id"]
                    # Navigate to the evaluation details page
                    st.switch_page("pages/5_View_Evaluation_Details.py")
            with cols[1]:
                st.write(row["created_at"])
            st.markdown(
                "<hr style='margin: 0; padding: 0; background-color: #333; height: 1px;'>",
                unsafe_allow_html=True,
            )
