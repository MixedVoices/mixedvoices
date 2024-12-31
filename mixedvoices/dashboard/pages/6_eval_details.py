# pages/evals/eval_details.py
import streamlit as st

from mixedvoices.dashboard.api.client import APIClient
from mixedvoices.dashboard.components.sidebar import Sidebar
from mixedvoices.dashboard.components.version_selector import render_version_selector


def eval_details_page():
    """Page to display evaluation details"""
    if (
        "current_project" not in st.session_state
        or "selected_eval_id" not in st.session_state
    ):
        st.switch_page("pages/5_evals_list.py")
        return

    api_client = APIClient()
    sidebar = Sidebar(api_client)
    sidebar.render()

    st.title(f"{st.session_state.current_project} | Evaluation Details")

    # Add back button
    if st.button("← Back to Evaluations"):
        st.session_state.selected_eval_id = None
        st.switch_page("pages/5_evals_list.py")

    # Optional version selection defaulting to "All Versions"
    selected_version = render_version_selector(
        api_client, st.session_state.current_project, optional=True, show_all=True
    )

    # Fetch eval details based on version selection
    if selected_version:
        eval_details = api_client.fetch_data(
            f"projects/{st.session_state.current_project}/evals/{st.session_state.selected_eval_id}/versions/{selected_version}"
        )
    else:
        eval_details = api_client.fetch_data(
            f"projects/{st.session_state.current_project}/evals/{st.session_state.selected_eval_id}"
        )

    if not eval_details:
        st.error("Failed to load evaluation details")
        return

    # Display sections
    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("Metrics")
        for metric in eval_details.get("metrics", []):
            st.write(f"- {metric['name']}")

    with col2:
        st.subheader("Prompts")
        for i, prompt in enumerate(eval_details.get("prompts", [])):
            st.text_area(f"Prompt {i+1}", prompt, height=100, disabled=True)

    # Eval Runs Section
    st.subheader("Evaluation Runs")

    if not eval_details.get("eval_runs"):
        st.info("No evaluation runs found.")
        return

    # Create columns for runs
    cols = st.columns(3)
    for i, run in enumerate(eval_details["eval_runs"]):
        with cols[i % 3]:
            with st.expander(f"Run {run['run_id']}", expanded=True):
                st.write("Version:", run.get("version_id", "N/A"))
                if st.button("View Details", key=f"view_run_{run['run_id']}"):
                    st.session_state.selected_run_id = run["run_id"]
                    st.switch_page("pages/7_eval_run_details.py")


if __name__ == "__main__":
    eval_details_page()
