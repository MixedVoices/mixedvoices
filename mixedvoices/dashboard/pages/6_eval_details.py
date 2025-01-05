import streamlit as st

from mixedvoices.dashboard.api.client import APIClient
from mixedvoices.dashboard.api.endpoints import eval_details_ep, version_eval_details_ep
from mixedvoices.dashboard.components.sidebar import Sidebar
from mixedvoices.dashboard.components.version_selector import render_version_selector
from mixedvoices.dashboard.utils import clear_selected_node_path, data_to_df_with_dates


@st.dialog("Metrics", width="large")
def render_metrics_dialog(metrics):
    """Render metrics in a dialog."""
    st.subheader("Metrics")
    for metric in metrics:
        st.write(f"- {metric}")


@st.dialog("Test Cases", width="large")
def render_test_cases_dialog(test_cases):
    """Render test cases in a dialog."""
    st.subheader("Test Cases")
    for i, test_case in enumerate(test_cases):
        st.text_area(f"Test Case {i+1}", test_case, height=200, disabled=True)


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
    st.markdown(f"#### Eval ID: {st.session_state.selected_eval_id}")
    if st.button("Back to Evaluators", icon=":material/arrow_back:"):
        st.session_state.selected_eval_id = None
        st.switch_page("pages/5_evals_list.py")

    all_eval_details = api_client.fetch_data(
        eval_details_ep(
            st.session_state.current_project, st.session_state.selected_eval_id
        )
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("View Metrics"):
            render_metrics_dialog(all_eval_details.get("metrics", []))
    with col2:
        if st.button("View Test Cases"):
            render_test_cases_dialog(all_eval_details.get("test_cases", []))

    # Evaluator Runs section
    st.markdown("#### Evaluator Runs")
    st.info(
        "💡 Different runs of the agent across the same test cases and metrics, use this to track progress."
    )

    selected_version = render_version_selector(
        api_client, st.session_state.current_project, optional=True, show_all=True
    )

    # Fetch eval details
    if selected_version:
        eval_details = api_client.fetch_data(
            version_eval_details_ep(
                st.session_state.current_project,
                selected_version,
                st.session_state.selected_eval_id,
            )
        )
    else:
        eval_details = all_eval_details

    if not eval_details:
        st.error("Failed to load evaluation details")
        return

    # Show dialogs if buttons were clicked
    if getattr(st.session_state, "show_metrics", False):
        render_metrics_dialog(eval_details.get("metrics", []))
        st.session_state.show_metrics = False

    if getattr(st.session_state, "show_test_cases", False):
        render_test_cases_dialog(eval_details.get("test_cases", []))
        st.session_state.show_test_cases = False

    eval_runs = eval_details.get("eval_runs", [])
    if not eval_runs:
        st.warning("No evaluator runs found.")
        return

    display_df = data_to_df_with_dates(eval_runs)

    # Add column headers
    header_col1, header_col2, header_col3 = st.columns([2, 2, 2])
    with header_col1:
        st.write("**Run ID**")
    with header_col2:
        st.write("**Created At**")
    with header_col3:
        st.write("**Version**")

    # Create a table for eval runs
    for idx, row in display_df.iterrows():
        col1, col2, col3 = st.columns([2, 2, 2])

        with col1:
            if st.button(
                row["run_id"],
                key=f"view_run_{row['run_id']}",
                help="Click to view run details",
            ):
                st.session_state.selected_run_id = row["run_id"]
                st.switch_page("pages/7_eval_run_details.py")

        with col2:
            st.write(row.get("created_at", "N/A"))

        with col3:
            st.write(row.get("version_id", "N/A"))
        st.markdown(
            "<hr style='margin: 0; padding: 0; background-color: #333;"
            " height: 1px;'>",
            unsafe_allow_html=True,
        )


if __name__ == "__main__":
    eval_details_page()
