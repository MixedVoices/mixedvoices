from typing import Dict, List, Optional

import streamlit as st


class MetricsManager:
    def __init__(self, api_client, project_id: Optional[str] = None):
        self.api_client = api_client
        self.project_id = project_id

    def _render_metric_row(
        self,
        metric: Dict,
        prefix: str,
        is_selectable: bool = False,
        is_editable: bool = False,
    ) -> Optional[Dict]:
        selected_metric = None

        if is_selectable:
            cols = st.columns([1, 30])
            with cols[0]:
                if st.checkbox("", key=f"{prefix}_{metric['name']}"):
                    selected_metric = metric
        else:
            cols = st.columns([1])
        container = cols[-1]

        with container:
            with st.expander(metric["name"]):
                if is_editable and st.session_state.get("is_editing", {}).get(
                    f"edit_{metric['name']}", False
                ):
                    self._render_edit_form(metric)
                else:
                    st.write("**Definition:**", metric["definition"])
                    st.write("**Scoring:**", metric["scoring"])
                    st.write("**Include Prompt:**", metric.get("include_prompt", False))
                    if is_editable:
                        if st.button("Edit Metric", key=f"edit_{metric['name']}"):
                            st.session_state.is_editing = st.session_state.get(
                                "is_editing", {}
                            )
                            st.session_state.is_editing[f"edit_{metric['name']}"] = True
                            st.rerun()

        return selected_metric

    def _render_edit_form(self, metric: Dict):
        new_definition = st.text_area(
            "Definition", value=metric["definition"], key=f"def_{metric['name']}"
        )
        new_scoring = st.selectbox(
            "Scoring Type",
            ["binary", "continuous"],
            index=0 if metric["scoring"] == "binary" else 1,
            key=f"score_{metric['name']}",
        )
        new_include_prompt = st.checkbox(
            "Include Prompt",
            value=metric.get("include_prompt", False),
            key=f"prompt_{metric['name']}",
        )

        cols = st.columns([1, 4])
        with cols[0]:
            if st.button("Save", key=f"save_{metric['name']}"):
                self.api_client.post_data(
                    f"projects/{self.project_id}/metrics/{metric['name']}",
                    {
                        "definition": new_definition,
                        "scoring": new_scoring,
                        "include_prompt": new_include_prompt,
                    },
                )
                st.session_state.is_editing[f"edit_{metric['name']}"] = False
                st.rerun()
        with cols[1]:
            if st.button("Cancel", key=f"cancel_{metric['name']}"):
                st.session_state.is_editing[f"edit_{metric['name']}"] = False
                st.rerun()

    def _render_add_metric_form(self, key_prefix: str = "") -> Optional[Dict]:
        with st.container():
            st.markdown("### Add New Metric")
            col1, col2 = st.columns(2)

            form_key = st.session_state.get(f"{key_prefix}form_key", 0)

            with col1:
                metric_name = st.text_input(
                    "Metric Name", key=f"{key_prefix}metric_name_{form_key}"
                )
                metric_scoring = st.selectbox(
                    "Scoring Type",
                    ["binary", "continuous"],
                    help="Binary for PASS/FAIL, Continuous for 0-10 scale",
                    key=f"{key_prefix}metric_scoring_{form_key}",
                )
                include_prompt = st.checkbox(
                    "Include Prompt",
                    key=f"{key_prefix}include_prompt_{form_key}",
                )
            with col2:
                metric_definition = st.text_area(
                    "Definition", key=f"{key_prefix}metric_def_{form_key}", height=100
                )

            if st.button("Add Metric", key=f"{key_prefix}add_btn_{form_key}"):
                if metric_name and metric_definition:
                    # Increment form key to reset fields
                    st.session_state[f"{key_prefix}form_key"] = form_key + 1
                    return {
                        "name": metric_name,
                        "definition": metric_definition,
                        "scoring": metric_scoring,
                        "include_prompt": include_prompt,
                    }
                st.error("Please provide both name and definition")
            return None

    def render(self, selection_mode: bool = False) -> Optional[List[Dict]]:
        selected_metrics = []

        if not self.project_id:
            if "custom_metrics" not in st.session_state:
                st.session_state.custom_metrics = []

            new_metric = self._render_add_metric_form("new_")
            if new_metric:
                st.session_state.custom_metrics.append(new_metric)
                st.rerun()

            st.divider()
            st.markdown("### Available Metrics")

            default_metrics = self.api_client.fetch_data("default_metrics").get(
                "metrics", []
            )
            if default_metrics:
                st.markdown("#### Default Metrics")
                for metric in default_metrics:
                    selected = self._render_metric_row(
                        metric, "default", is_selectable=True
                    )
                    if selected:
                        selected_metrics.append(selected)

            if st.session_state.custom_metrics:
                st.markdown("#### Custom Metrics")
                for metric in st.session_state.custom_metrics:
                    selected = self._render_metric_row(
                        metric, "custom", is_selectable=True
                    )
                    if selected:
                        selected_metrics.append(selected)

            metric_names = [m["name"] for m in selected_metrics]
            if len(metric_names) != len(set(metric_names)):
                st.error(
                    "You have multipe metrics with the same name which isn't allowed"
                )
                return None

        else:
            new_metric = self._render_add_metric_form("project_")
            if new_metric:
                existing_names = [
                    m["name"]
                    for m in self.api_client.fetch_data(
                        f"projects/{self.project_id}/metrics"
                    ).get("metrics", [])
                ]

                if new_metric["name"] in existing_names:
                    st.error("A metric with this name already exists")
                else:
                    response = self.api_client.post_data(
                        f"projects/{self.project_id}/metrics", new_metric
                    )
                    if response.get("message"):
                        st.success("Metric added successfully!")
                        st.rerun()

            project_metrics = self.api_client.fetch_data(
                f"projects/{self.project_id}/metrics"
            ).get("metrics", [])

            st.write("### Current Metrics")
            for metric in project_metrics:
                self._render_metric_row(metric, "project", is_editable=True)

        return selected_metrics if selection_mode else None
