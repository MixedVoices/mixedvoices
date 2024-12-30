import streamlit as st


def render_metrics_list(api_client, project_id: str, selection_mode: bool = False):
    """Render metrics list with optional selection mode"""
    metrics = api_client.fetch_data(f"projects/{project_id}/metrics")

    if selection_mode:
        selected_metrics = []
        for metric in metrics["metrics"]:
            if st.checkbox(f"Select {metric['name']}", key=f"metric_{metric['name']}"):
                selected_metrics.append(metric["name"])
        return selected_metrics
    else:
        for metric in metrics["metrics"]:
            with st.expander(metric["name"]):
                st.write("Definition:", metric["definition"])
                st.write("Scoring:", metric["scoring"])
