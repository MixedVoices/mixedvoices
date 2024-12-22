import streamlit as st

from mixedvoices.dashboard.api.client import APIClient
from mixedvoices.dashboard.api.endpoints import (
    list_eval_runs_endpoint,
)
from mixedvoices.dashboard.components.evaluation_viewer import EvaluationViewer
from mixedvoices.dashboard.utils import disable_evaluation_details_page


def evaluations_page():
    if (
        "current_project" not in st.session_state
        or "current_version" not in st.session_state
    ):
        st.switch_page("Home.py")
        return
    disable_evaluation_details_page()

    st.title(f"{st.session_state.current_project} | {st.session_state.current_version}")

    # Initialize API client and components
    api_client = APIClient()
    evaluation_viewer = EvaluationViewer(
        api_client, st.session_state.current_project, st.session_state.current_version
    )

    # Display all evaluation runs
    eval_runs_data = api_client.fetch_data(
        list_eval_runs_endpoint(
            st.session_state.current_project, st.session_state.current_version
        )
    )

    if eval_runs_data.get("eval_runs"):
        evaluation_viewer.display_evaluations_list(eval_runs_data["eval_runs"])
    else:
        st.info(
            "No evaluation runs found for this version. "
            "Run evaluations using the Python API to see results here."
        )


if __name__ == "__main__":
    evaluations_page()
