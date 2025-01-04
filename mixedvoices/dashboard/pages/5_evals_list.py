import streamlit as st

from mixedvoices.dashboard.api.client import APIClient
from mixedvoices.dashboard.api.endpoints import evals_ep
from mixedvoices.dashboard.components.evaluator_viewer import EvaluatorViewer
from mixedvoices.dashboard.components.sidebar import Sidebar
from mixedvoices.dashboard.utils import clear_selected_node_path


def evals_list_page():
    if "current_project" not in st.session_state:
        st.switch_page("app.py")
        return

    api_client = APIClient()
    clear_selected_node_path()
    sidebar = Sidebar(api_client)
    sidebar.render()

    st.title("Evaluators")
    st.info(
        "💡 Evaluators are reusable collections of tests and metrics to test model performance."
    )
    st.info(
        "Load in python using project.load_evaluator(eval_id)",
        icon=":material/developer_guide:",
    )

    evaluator_viewer = EvaluatorViewer(api_client)

    # Fetch evaluations
    evals_data = api_client.fetch_data(evals_ep(st.session_state.current_project))

    if evals_data.get("evals"):
        evaluator_viewer.display_evaluator_list(evals_data["evals"])
    else:
        st.warning("No evaluations found. Create one using the Create Evaluator page.")


if __name__ == "__main__":
    evals_list_page()
