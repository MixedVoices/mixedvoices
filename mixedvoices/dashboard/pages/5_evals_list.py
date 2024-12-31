import streamlit as st

from mixedvoices.dashboard.api.client import APIClient
from mixedvoices.dashboard.components.evaluator_viewer import EvaluatorViewer
from mixedvoices.dashboard.components.sidebar import Sidebar


def evals_list_page():
    if "current_project" not in st.session_state:
        st.switch_page("Home.py")
        return

    api_client = APIClient()
    sidebar = Sidebar(api_client)
    sidebar.render()

    st.title("Evaluators")

    evaluator_viewer = EvaluatorViewer(api_client)

    # Fetch evaluations
    evals_data = api_client.fetch_data(
        f"projects/{st.session_state.current_project}/evals"
    )

    if evals_data.get("evals"):
        evaluator_viewer.display_evaluator_list(evals_data["evals"])
    else:
        st.info("No evaluations found. Create one using the Create Evaluator page.")


if __name__ == "__main__":
    evals_list_page()
