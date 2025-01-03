import streamlit as st

from mixedvoices.dashboard.api.client import APIClient
from mixedvoices.dashboard.utils import data_to_df_with_dates


class EvaluatorViewer:
    def __init__(self, api_client: APIClient):
        self.api_client = api_client

    def display_evaluator_list(self, evals: list) -> None:
        """Display list of recordings with details"""
        # Create DataFrame and format dates
        display_df = data_to_df_with_dates(evals)

        # Table header
        header_cols = st.columns([3, 1.5, 1.2, 1.2, 7])
        with header_cols[0]:
            st.markdown("**Evaluator ID**")
        with header_cols[1]:
            st.markdown("**Created At**")
        with header_cols[2]:
            st.markdown("**Num Prompts**")
        with header_cols[3]:
            st.markdown("**Num Runs**")
        with header_cols[4]:
            st.markdown("**Metrics**")
        st.markdown(
            "<hr style='margin: 0; padding: 0; background-color: #333; height: 1px;'>",
            unsafe_allow_html=True,
        )

        # Table rows
        for _idx, row in display_df.iterrows():
            cols = st.columns([3, 1.5, 1.2, 1.2, 7])
            with cols[0]:
                eval_id = row["eval_id"]
                if st.button(
                    eval_id, key=f"view_{eval_id}", help="Click to view details"
                ):
                    st.session_state.selected_eval_id = eval_id
                    st.switch_page("pages/6_eval_details.py")
            with cols[1]:
                st.write(row["created_at"])
            with cols[2]:
                st.write(row["num_prompts"])
            with cols[3]:
                st.write(row["num_eval_runs"])
            with cols[4]:
                metric_names = row["metric_names"]
                metric_names_str = ", ".join(metric_names)
                st.write(metric_names_str)
            st.markdown(
                "<hr style='margin: 0; padding: 0; background-color: #333;"
                " height: 1px;'>",
                unsafe_allow_html=True,
            )
