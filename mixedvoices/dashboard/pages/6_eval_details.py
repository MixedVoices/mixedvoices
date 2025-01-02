import streamlit as st

from mixedvoices.dashboard.api.client import APIClient
from mixedvoices.dashboard.components.sidebar import Sidebar
from mixedvoices.dashboard.components.version_selector import render_version_selector
from mixedvoices.dashboard.utils import clear_selected_node_path


@st.dialog("Metrics", width="large")
def render_metrics_dialog(metrics):
    """Render metrics in a dialog."""
    st.subheader("Metrics")
    for metric in metrics:
        st.write(f"- {metric['name']}")


@st.dialog("Prompts", width="large")
def render_prompts_dialog(prompts):
    """Render prompts in a dialog."""
    st.subheader("Prompts")
    for i, prompt in enumerate(prompts):
        st.text_area(f"Prompt {i+1}", prompt, height=200, disabled=True)


def eval_details_page():
    """Page to display evaluation details"""
    if (
        "current_project" not in st.session_state
        or "selected_eval_id" not in st.session_state
        or st.session_state.selected_eval_id is None
    ):
        st.switch_page("pages/5_evals_list.py")
        return

    api_client = APIClient()
    clear_selected_node_path()
    sidebar = Sidebar(api_client)
    sidebar.render()

    # Page header and navigation
    st.title("Evaluator Details")
    if st.button("Back to Evaluators", icon=":material/arrow_back:"):
        st.session_state.selected_eval_id = None
        st.switch_page("pages/5_evals_list.py")

    st.markdown(f"#### Eval ID: {st.session_state.selected_eval_id}")

    selected_version = render_version_selector(
        api_client, st.session_state.current_project, optional=True, show_all=True
    )

    # Fetch eval details
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

    # Metrics and Prompts buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("View Metrics"):
            render_metrics_dialog(eval_details.get("metrics", []))
    with col2:
        if st.button("View Prompts"):
            render_prompts_dialog(eval_details.get("prompts", []))

    # Show dialogs if buttons were clicked
    if getattr(st.session_state, "show_metrics", False):
        render_metrics_dialog(eval_details.get("metrics", []))
        st.session_state.show_metrics = False

    if getattr(st.session_state, "show_prompts", False):
        render_prompts_dialog(eval_details.get("prompts", []))
        st.session_state.show_prompts = False

    # Evaluator Runs section
    st.subheader("Evaluator Runs")
    # st.info()

    eval_runs = eval_details.get("eval_runs", [])
    if not eval_runs:
        st.warning("No evaluator runs found.")
        return

    # Add column headers
    header_col1, header_col2, header_col3 = st.columns([2, 2, 2])
    with header_col1:
        st.write("**Run ID**")
    with header_col2:
        st.write("**Created At**")
    with header_col3:
        st.write("**Version**")

    # Create a table for eval runs
    for run in eval_runs:
        col1, col2, col3 = st.columns([2, 2, 2])

        with col1:
            if st.button(
                run["run_id"],
                key=f"view_run_{run['run_id']}",
                help="Click to view run details",
            ):
                st.session_state.selected_run_id = run["run_id"]
                st.switch_page("pages/7_eval_run_details.py")

        with col2:
            st.write(run.get("created_at", "N/A"))

        with col3:
            st.write(run.get("version_id", "N/A"))
        st.markdown(
            "<hr style='margin: 0; padding: 0; background-color: #333;"
            " height: 1px;'>",
            unsafe_allow_html=True,
        )


if __name__ == "__main__":
    eval_details_page()
