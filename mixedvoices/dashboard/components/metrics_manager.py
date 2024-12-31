from typing import List, Optional

import streamlit as st


# metrics_manager.py
class MetricsManager:
    def __init__(self, api_client, project_id: Optional[str] = None):
        self.api_client = api_client
        self.project_id = project_id

    def render(self, selection_mode: bool = False) -> Optional[List[str]]:
        selected_metrics = []

        if self.project_id:
            project_metrics = self.api_client.fetch_data(
                f"projects/{self.project_id}/metrics"
            )
            project_metrics = project_metrics.get("metrics", [])
        else:
            project_metrics = []

        default_metrics = self.api_client.fetch_data("default_metrics")
        default_metrics = default_metrics.get("metrics", [])

        if not self.project_id:
            # Initialize custom metrics list in session state
            if "custom_metrics" not in st.session_state:
                st.session_state.custom_metrics = []

            col1, col2 = st.columns([1, 2])

            with col1:
                st.subheader("Select Metrics")

                if default_metrics:
                    st.markdown("##### Default Metrics")
                    for metric in default_metrics:
                        if st.checkbox(
                            f"{metric['name']}", key=f"default_{metric['name']}"
                        ):
                            selected_metrics.append(metric["name"])

                if st.session_state.custom_metrics:
                    st.markdown("##### Custom Metrics")
                    for metric in st.session_state.custom_metrics:
                        if st.checkbox(
                            f"{metric['name']}", key=f"custom_{metric['name']}"
                        ):
                            selected_metrics.append(metric["name"])

            with col2:
                st.markdown("### Add New Metric")
                metric_name = st.text_input("Metric Name")
                metric_definition = st.text_area("Definition")
                metric_scoring = st.selectbox(
                    "Scoring Type",
                    ["binary", "continuous"],
                    help="Binary for PASS/FAIL, Continuous for 0-10 scale",
                )

                if st.button("Add Metric"):
                    if metric_name and metric_definition:
                        st.session_state.custom_metrics.append(
                            {
                                "name": metric_name,
                                "definition": metric_definition,
                                "scoring": metric_scoring,
                            }
                        )
                        st.rerun()
                    else:
                        st.error("Please provide both name and definition")

            # Validate selection
            if len(selected_metrics) != len(set(selected_metrics)):
                st.error("You have selected duplicate metrics")
                return None

        else:
            # Project Metrics Page Mode
            st.markdown("### Add New Metric")

            metric_name = st.text_input("Metric Name")
            metric_definition = st.text_area("Definition")
            metric_scoring = st.selectbox(
                "Scoring Type",
                ["binary", "continuous"],
                help="Binary for PASS/FAIL, Continuous for 0-10 scale",
            )

            if st.button("Add Metric"):
                if metric_name and metric_definition:
                    # Check for existing metric
                    existing_names = [m["name"] for m in project_metrics]
                    if metric_name in existing_names:
                        st.error("A metric with this name already exists")
                        return None

                    response = self.api_client.post_data(
                        f"projects/{self.project_id}/metrics",
                        {
                            "name": metric_name,
                            "definition": metric_definition,
                            "scoring": metric_scoring,
                        },
                    )
                    if response.get("message"):
                        st.success("Metric added successfully!")
                        st.rerun()
                else:
                    st.error("Please provide both name and definition")

            # Display existing metrics
            st.write("### Current Metrics")
            for metric in project_metrics:
                with st.expander(metric["name"], expanded=False):
                    if "is_editing" not in st.session_state:
                        st.session_state.is_editing = {}

                    metric_id = f"edit_{metric['name']}"

                    if st.session_state.is_editing.get(metric_id, False):
                        # Edit mode
                        new_definition = st.text_area(
                            "Definition",
                            value=metric["definition"],
                            key=f"def_{metric_id}",
                        )
                        new_scoring = st.selectbox(
                            "Scoring Type",
                            ["binary", "continuous"],
                            index=0 if metric["scoring"] == "binary" else 1,
                            key=f"score_{metric_id}",
                        )

                        col1, col2 = st.columns([1, 4])
                        with col1:
                            if st.button("Save", key=f"save_{metric_id}"):
                                self.api_client.post_data(
                                    f"projects/{self.project_id}/metrics/{metric['name']}",
                                    {
                                        "definition": new_definition,
                                        "scoring": new_scoring,
                                    },
                                )
                                st.session_state.is_editing[metric_id] = False
                                st.rerun()
                        with col2:
                            if st.button("Cancel", key=f"cancel_{metric_id}"):
                                st.session_state.is_editing[metric_id] = False
                                st.rerun()
                    else:
                        # View mode
                        st.write("**Definition:**", metric["definition"])
                        st.write("**Scoring:**", metric["scoring"])

                        col1, col2 = st.columns([1, 20])
                        with col1:
                            if st.button("✏️", key=f"edit_{metric_id}"):
                                st.session_state.is_editing[metric_id] = True
                                st.rerun()

        return selected_metrics if selection_mode else None
