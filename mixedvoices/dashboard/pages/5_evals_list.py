import streamlit as st

from mixedvoices.dashboard.api.client import APIClient
from mixedvoices.dashboard.components.sidebar import Sidebar


def evals_list_page():
    if "current_project" not in st.session_state:
        st.switch_page("Home.py")
        return

    api_client = APIClient()
    sidebar = Sidebar(api_client)
    sidebar.render()

    st.title("Evaluators")

    # Fetch evaluations
    evals_data = api_client.fetch_data(
        f"projects/{st.session_state.current_project}/evals"
    )

    if evals_data.get("evals"):
        for eval_item in evals_data["evals"]:
            with st.expander(f"Evaluator {eval_item['eval_id']}", expanded=False):
                st.write(f"Created: {eval_item['created_at']}")
                st.write(f"Number of prompts: {eval_item['num_prompts']}")
                st.write(f"Number of runs: {eval_item['num_eval_runs']}")
                st.write("Metrics:")
                for metric in eval_item["metric_names"]:
                    st.write(f"- {metric}")

                if st.button("View Details", key=f"view_{eval_item['eval_id']}"):
                    st.session_state.selected_eval_id = eval_item["eval_id"]
                    st.switch_page("pages/6_eval_details.py")
    else:
        st.info("No evaluations found. Create one using the Create Evaluator page.")


if __name__ == "__main__":
    evals_list_page()
