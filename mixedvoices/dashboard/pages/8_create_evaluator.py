import streamlit as st

from mixedvoices.dashboard.api.client import APIClient
from mixedvoices.dashboard.components.metrics_manager import MetricsManager
from mixedvoices.dashboard.components.sidebar import Sidebar
from mixedvoices.dashboard.utils import clear_selected_node_path


def create_evaluator_page():
    if "current_project" not in st.session_state:
        st.switch_page("Home.py")
        return

    api_client = APIClient()
    clear_selected_node_path()
    sidebar = Sidebar(api_client)
    sidebar.render()

    st.title("Create Evaluator")

    # Initialize state for prompts
    if "eval_prompts" not in st.session_state:
        st.session_state.eval_prompts = [""]

    # Prompts section
    st.subheader("Evaluator Prompts")

    prompts_to_remove = []
    for i, prompt in enumerate(st.session_state.eval_prompts):
        col1, col2 = st.columns([6, 1])
        with col1:
            st.session_state.eval_prompts[i] = st.text_area(
                f"Prompt {i+1}", prompt, key=f"prompt_{i}"
            )
        with col2:
            if len(st.session_state.eval_prompts) > 1:
                if st.button("Remove", key=f"remove_{i}"):
                    prompts_to_remove.append(i)

    # Handle prompt removals
    for idx in reversed(prompts_to_remove):
        st.session_state.eval_prompts.pop(idx)

    if st.button("Add Prompt"):
        st.session_state.eval_prompts.append("")
        st.rerun()

    # Metrics selection
    st.subheader("Select Metrics")
    metrics_manager = MetricsManager(api_client, st.session_state.current_project)
    selected_metrics = metrics_manager.render(selection_mode=True)

    if st.button("Create Evaluator"):
        # Validate inputs
        valid_prompts = [p for p in st.session_state.eval_prompts if p.strip()]
        if not valid_prompts:
            st.error("Please add at least one prompt")
            return

        if not selected_metrics:
            st.error("Please select at least one metric")
            return

        # Create evaluator
        response = api_client.post_data(
            f"projects/{st.session_state.current_project}/evals",
            {"eval_prompts": valid_prompts, "metric_names": selected_metrics},
        )

        if response.get("eval_id"):
            st.success("Evaluator created successfully!")
            st.session_state.eval_prompts = [""]  # Reset prompts
            st.rerun()


if __name__ == "__main__":
    create_evaluator_page()
