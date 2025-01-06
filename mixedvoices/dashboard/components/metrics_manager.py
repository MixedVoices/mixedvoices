from typing import Dict, List, Optional

import streamlit as st

from mixedvoices.dashboard.api.endpoints import (
    default_metrics_ep,
    metric_ep,
    project_metrics_ep,
)


class MetricsManager:
    def __init__(self, api_client, project_id: Optional[str] = None):
        self.api_client = api_client
        self.project_id = project_id

    def _get_all_metrics(self) -> List[Dict]:
        """Helper method to get all available metrics"""
        all_metrics = []
        if self.project_id:
            project_metrics = self.api_client.fetch_data(
                project_metrics_ep(self.project_id)
            ).get("metrics", [])
            all_metrics.extend((m, "project") for m in project_metrics)
        else:
            default_metrics = self.api_client.fetch_data(default_metrics_ep()).get(
                "metrics", []
            )
            all_metrics.extend((m, "default") for m in default_metrics)
            if "custom_metrics" in st.session_state:
                all_metrics.extend(
                    (m, "custom") for m in st.session_state.custom_metrics
                )
        return all_metrics

    def _handle_select_all_change(self):
        """Handle select all checkbox state change"""
        all_metrics = self._get_all_metrics()
        for metric, prefix in all_metrics:
            st.session_state[f"{prefix}_{metric['name']}"] = (
                st.session_state.select_all_metrics
            )

    def _handle_individual_change(self, checkbox_key: str):
        """Handle individual checkbox state change"""
        if not st.session_state[checkbox_key]:
            st.session_state.select_all_metrics = False

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
            checkbox_key = f"{prefix}_{metric['name']}"

            # Initialize checkbox state if not present
            if checkbox_key not in st.session_state:
                st.session_state[checkbox_key] = False

            with cols[0]:
                if st.checkbox(
                    "Selection checkbox",
                    key=checkbox_key,
                    label_visibility="collapsed",
                    on_change=self._handle_individual_change,
                    args=(checkbox_key,),
                ):
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
                        if st.button(
                            "Edit",
                            key=f"edit_{metric['name']}",
                            icon=":material/edit:",
                        ):
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
            if st.button("Save", key=f"save_{metric['name']}", icon=":material/check:"):
                if self.project_id:
                    # Update through API for project metrics
                    self.api_client.post_data(
                        metric_ep(self.project_id, metric["name"]),
                        {
                            "definition": new_definition,
                            "scoring": new_scoring,
                            "include_prompt": new_include_prompt,
                        },
                    )
                else:
                    # Update in memory for custom metrics
                    for idx, m in enumerate(st.session_state.custom_metrics):
                        if m["name"] == metric["name"]:
                            st.session_state.custom_metrics[idx].update(
                                {
                                    "definition": new_definition,
                                    "scoring": new_scoring,
                                    "include_prompt": new_include_prompt,
                                }
                            )
                            break

                st.session_state.is_editing[f"edit_{metric['name']}"] = False
                st.rerun()
        with cols[1]:
            if st.button(
                "Cancel", key=f"cancel_{metric['name']}", icon=":material/close:"
            ):
                st.session_state.is_editing[f"edit_{metric['name']}"] = False
                st.rerun()

    def _render_add_metric_form(self) -> Optional[Dict]:
        with st.expander("Add New Metric", icon=":material/add:"):
            col1, col2, col3 = st.columns([1, 1, 4])

            if "new_form_key" not in st.session_state:
                st.session_state.new_form_key = 0
            form_key = st.session_state.new_form_key

            with col1:
                metric_name = st.text_input(
                    "Metric Name", key=f"new_metric_name_{form_key}"
                )
                include_prompt = st.checkbox(
                    "Include Prompt",
                    key=f"new_include_prompt_{form_key}",
                    help="If the agent prompt must be passed to judge the score",
                )
            with col2:
                metric_scoring = st.selectbox(
                    "Scoring Type",
                    ["binary", "continuous"],
                    help="Binary for PASS/FAIL, Continuous for 0-10 scale",
                    key=f"new_metric_scoring_{form_key}",
                )
            with col3:
                metric_definition = st.text_area(
                    "Definition", key=f"new_metric_def_{form_key}", height=100
                )

            if st.button("Add Metric", key=f"new_add_btn_{form_key}"):
                if metric_name and metric_definition:
                    # Increment form key to reset fields
                    st.session_state.new_form_key = form_key + 1
                    return {
                        "name": metric_name,
                        "definition": metric_definition,
                        "scoring": metric_scoring,
                        "include_prompt": include_prompt,
                    }
                st.error("Please provide both name and definition")
            return None

    def render(
        self, selection_mode: bool = True, creation_mode: bool = True
    ) -> Optional[List[Dict]]:
        if not selection_mode and not creation_mode:
            raise ValueError(
                "At least one of selection_mode or creation_mode must be True"
            )
        selected_metrics = []

        # For creation-only or selection-only modes, project_id is required
        if (creation_mode != selection_mode) and not self.project_id:
            raise ValueError(
                "Project ID is required for creation-only or selection-only modes"
            )

        # Initialize custom metrics in session state if working in memory
        if not self.project_id and "custom_metrics" not in st.session_state:
            st.session_state.custom_metrics = []

        # Handle creation mode
        if creation_mode:
            new_metric = self._render_add_metric_form()
            if new_metric:
                if self.project_id:
                    # Add through API for project metrics
                    existing_metrics = self.api_client.fetch_data(
                        project_metrics_ep(self.project_id)
                    ).get("metrics", [])

                    if any(m["name"] == new_metric["name"] for m in existing_metrics):
                        st.error("A metric with this name already exists")
                    else:
                        response = self.api_client.post_data(
                            project_metrics_ep(self.project_id), new_metric
                        )
                        if response.get("message"):
                            st.success("Metric added successfully!")
                            st.rerun()
                else:
                    # Add to memory for custom metrics
                    if any(
                        m["name"] == new_metric["name"]
                        for m in st.session_state.custom_metrics
                    ):
                        st.error("A metric with this name already exists")
                    else:
                        st.session_state.custom_metrics.append(new_metric)
                        st.rerun()

        # Add Select All checkbox if in selection mode
        if selection_mode:
            # Initialize select_all state if not present
            if "select_all_metrics" not in st.session_state:
                st.session_state.select_all_metrics = False

            st.checkbox(
                "Select All Metrics",
                key="select_all_metrics",
                on_change=self._handle_select_all_change,
            )

        # Show metrics based on mode and project_id
        if self.project_id:
            st.markdown("#### Existing Metrics")
            # Project mode: fetch and display project metrics
            project_metrics = self.api_client.fetch_data(
                project_metrics_ep(self.project_id)
            ).get("metrics", [])
            for metric in project_metrics:
                selected = self._render_metric_row(
                    metric,
                    "project",
                    is_selectable=selection_mode,
                    is_editable=creation_mode,
                )
                if selected:
                    selected_metrics.append(selected)
        else:
            default_metrics = self.api_client.fetch_data(default_metrics_ep()).get(
                "metrics", []
            )
            if default_metrics:
                st.markdown("#### Default Metrics")
                for metric in default_metrics:
                    selected = self._render_metric_row(
                        metric, "default", is_selectable=selection_mode
                    )
                    if selected:
                        selected_metrics.append(selected)

            if st.session_state.custom_metrics:
                st.markdown("#### Custom Metrics")
                for metric in st.session_state.custom_metrics:
                    selected = self._render_metric_row(
                        metric,
                        "custom",
                        is_selectable=selection_mode,
                        is_editable=creation_mode,
                    )
                    if selected:
                        selected_metrics.append(selected)

        # Check for fully selected state and update select_all accordingly
        if selection_mode:
            all_metrics = self._get_all_metrics()
            all_selected = all(
                st.session_state.get(f"{prefix}_{metric['name']}", False)
                for metric, prefix in all_metrics
            )
            if all_selected and not st.session_state.select_all_metrics:
                st.session_state.select_all_metrics = True

        # Validate no duplicate metric names if in selection mode
        if selection_mode:
            metric_names = [m["name"] for m in selected_metrics]
            if len(metric_names) != len(set(metric_names)):
                st.error(
                    "You have multiple metrics with the same name which isn't allowed"
                )
                return None

        return selected_metrics if selection_mode else None
