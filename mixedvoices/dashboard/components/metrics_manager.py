from typing import List, Optional

import streamlit as st


class MetricsManager:
    def __init__(self, api_client, project_id: Optional[str] = None):
        self.api_client = api_client
        self.project_id = project_id

    def render(self, selection_mode: bool = False) -> Optional[List[str]]:
        """Render metrics management interface

        Args:
            selection_mode: If True, allows metric selection and returns selected metrics

        Returns:
            List of selected metric names if in selection mode, None otherwise
        """
        selected_metrics = []

        # Fetch metrics
        if self.project_id:
            project_metrics = self.api_client.fetch_data(
                f"projects/{self.project_id}/metrics"
            )
            project_metrics = project_metrics.get("metrics", [])
        else:
            project_metrics = []

        default_metrics = self.api_client.fetch_data("default_metrics")
        default_metrics = default_metrics.get("metrics", [])

        # Combine and deduplicate metrics
        all_metrics = {m["name"]: m for m in project_metrics}
        for metric in default_metrics:
            if metric["name"] not in all_metrics:
                all_metrics[metric["name"]] = metric

        # Add/Update Metric Interface
        with st.expander("Add/Update Metric", expanded=False):
            metric_name = st.text_input("Metric Name")
            if metric_name in all_metrics:
                st.info(f"Updating existing metric: {metric_name}")

            metric_definition = st.text_area("Definition")
            metric_scoring = st.selectbox(
                "Scoring Type",
                ["binary", "continuous"],
                help="Binary for PASS/FAIL, Continuous for 0-10 scale",
            )

            if st.button("Save Metric"):
                if metric_name and metric_definition:
                    if self.project_id:
                        if metric_name in all_metrics:
                            self.api_client.post_data(
                                f"projects/{self.project_id}/metrics/{metric_name}",
                                {
                                    "definition": metric_definition,
                                    "scoring": metric_scoring,
                                },
                            )
                        else:
                            self.api_client.post_data(
                                f"projects/{self.project_id}/metrics",
                                {
                                    "name": metric_name,
                                    "definition": metric_definition,
                                    "scoring": metric_scoring,
                                },
                            )
                        st.success("Metric saved successfully!")
                        st.rerun()
                else:
                    st.error("Please provide both name and definition")

        # Display/Select Metrics
        st.write("### Available Metrics")

        if selection_mode:
            # Selection mode - use checkboxes
            for metric_name, metric in all_metrics.items():
                col1, col2 = st.columns([6, 1])

                with col1:
                    with st.expander(metric_name):
                        st.write("**Definition:**", metric["definition"])
                        st.write("**Scoring:**", metric["scoring"])

                with col2:
                    if st.checkbox(
                        "Select",
                        key=f"select_{metric_name}",
                        help=f"Select {metric_name} metric",
                    ):
                        selected_metrics.append(metric_name)
        else:
            # View mode - just show metrics
            for metric_name, metric in all_metrics.items():
                with st.expander(metric_name):
                    st.write("**Definition:**", metric["definition"])
                    st.write("**Scoring:**", metric["scoring"])

                    if st.button("Update", key=f"update_{metric_name}"):
                        # Pre-fill the add/update form
                        st.session_state.update_metric = metric
                        st.rerun()

        return selected_metrics if selection_mode else None
