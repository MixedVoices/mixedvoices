from typing import List

import streamlit as st

from mixedvoices.dashboard.api.client import APIClient
from mixedvoices.dashboard.api.endpoints import evals_ep, prompt_generator_ep
from mixedvoices.dashboard.components.sidebar import Sidebar
from mixedvoices.dashboard.utils import clear_selected_node_path


def generate_prompt(
    api_client,
    prompt_data: dict,
    agent_prompt: str,
    user_demographic_info: str = None,
    file=None,
) -> List[str]:
    generation_data = {
        "agent_prompt": agent_prompt,
        "user_demographic_info": user_demographic_info,
        "transcript": None,
        "user_channel": None,
        "description": None,
        "edge_case_count": None,
    }

    if prompt_data["type"] == "plain_text":
        return [prompt_data["content"]]

    if prompt_data["type"] == "transcript":
        generation_data["transcript"] = prompt_data["content"]
    elif prompt_data["type"] == "recording":
        generation_data["user_channel"] = prompt_data["user_channel"]
    elif prompt_data["type"] == "edge_cases":
        generation_data["edge_case_count"] = prompt_data["count"]
    elif prompt_data["type"] == "description":
        generation_data["description"] = prompt_data["content"]

    files = {"file": file} if file else None
    response = api_client.post_data(
        prompt_generator_ep(), files=files, params=generation_data
    )
    return response.get("prompts", [])


def prompt_creation_dialog(api_client):
    if "is_generating" not in st.session_state:
        st.session_state.is_generating = False
    if "pending_generation" not in st.session_state:
        st.session_state.pending_generation = None
    if "show_success" not in st.session_state:
        st.session_state.show_success = False

    with st.expander("Create New Test Case", expanded=True):
        # Create a container for status messages
        status_container = st.empty()

        # Show and clear success message if needed
        if st.session_state.show_success:
            status_container.success("Test Case(s) generated successfully!")
            st.session_state.show_success = False

        # Handle pending generation from previous run
        if st.session_state.is_generating and st.session_state.pending_generation:
            status_container.info("Generating test case(s)...", icon="🔄")

            try:
                generation_data = st.session_state.pending_generation
                prompts = generate_prompt(
                    api_client,
                    generation_data["data"],
                    st.session_state.agent_prompt,
                    st.session_state.user_demographic_info,
                    file=generation_data.get("file"),
                )
                # Clear generation state and show success
                st.session_state.is_generating = False
                st.session_state.pending_generation = None
                st.session_state.show_success = True
                return [
                    {"type": generation_data["type"], "content": prompt}
                    for prompt in prompts
                ]
            except Exception as e:
                status_container.error(f"Generation failed: {str(e)}")
                st.session_state.is_generating = False
                st.session_state.pending_generation = None
                st.rerun()

        tabs = st.tabs(
            ["Plain Text", "Transcript", "Recording", "Edge Cases", "Description"]
        )

        with tabs[0]:
            st.info(
                "💡 Define the exact test case. Include things like name, age, personality traits, call objective, call path"
            )
            prompt = st.text_area(
                "Enter test case", disabled=st.session_state.is_generating
            )
            if st.button(
                "Add Test Case",
                disabled=st.session_state.is_generating,
                key="plain_text_tests",
            ):
                if prompt:
                    st.session_state.is_generating = True
                    st.session_state.show_success = True
                    return [{"type": "plain_text", "content": prompt}]

        with tabs[1]:
            st.info(
                "💡 Generate a test case from a call transcript. Transcript should have labels for each utterance . Use 'user:', 'bot:' labels"
            )
            transcript = st.text_area(
                "Enter the transcript", disabled=st.session_state.is_generating
            )
            if st.button(
                "Generate Test Case",
                disabled=st.session_state.is_generating,
                key="transcript_tests",
            ):
                if transcript:
                    st.session_state.is_generating = True
                    st.session_state.pending_generation = {
                        "type": "transcript",
                        "data": {"type": "transcript", "content": transcript},
                    }
                    st.rerun()

        with tabs[2]:
            st.info(
                "💡 Generate a test case from an existing call. Use a stereo recording with user and bot on different channels."
            )
            uploaded_file = st.file_uploader(
                "Upload recording file",
                type=["wav", "mp3"],
                disabled=st.session_state.is_generating,
            )
            user_channel = st.selectbox(
                "Select user channel",
                ["left", "right"],
                disabled=st.session_state.is_generating,
            )
            if st.button(
                "Generate Test Case",
                disabled=st.session_state.is_generating,
                key="recording_tests",
            ):
                if uploaded_file:
                    st.session_state.is_generating = True
                    st.session_state.pending_generation = {
                        "type": "recording",
                        "data": {
                            "type": "recording",
                            "user_channel": user_channel,
                        },
                        "file": uploaded_file,
                    }
                    st.rerun()

        with tabs[3]:
            st.info(
                "💡 Generate test cases for edge cases where bot might fail or behave unexpectedly"
            )
            count = st.number_input(
                "Number of edge cases",
                min_value=1,
                value=1,
                disabled=st.session_state.is_generating,
            )
            if st.button(
                "Generate Test Cases",
                disabled=st.session_state.is_generating,
                key="edge_cases_tests",
            ):
                st.session_state.is_generating = True
                st.session_state.pending_generation = {
                    "type": "edge_cases",
                    "data": {"type": "edge_cases", "count": count},
                }
                st.rerun()

        with tabs[4]:
            st.info("💡 Generate a test case based on a rough description.")
            description = st.text_area(
                "Enter description", disabled=st.session_state.is_generating
            )
            if st.button(
                "Generate Test Case",
                disabled=st.session_state.is_generating,
                key="description_tests",
            ):
                if description:
                    st.session_state.is_generating = True
                    st.session_state.pending_generation = {
                        "type": "description",
                        "data": {"type": "description", "content": description},
                    }
                    st.rerun()

    return None


def display_prompts(prompts: List[dict], selected_prompts: List[int]):
    if not prompts:
        st.write("No test cases created yet")
        return

    if prompts:  # Only show clear button if there are prompts
        if st.button("Clear All Test Cases", type="secondary", key="clear_all_prompts"):
            prompts.clear()
            selected_prompts.clear()
            st.rerun()

    col1, col2, col3 = st.columns([1, 20, 3])
    with col1:
        st.write("Select")
    with col2:
        st.write("Prompt")
    with col3:
        st.write("Created From")

    st.markdown(
        "<hr style='margin: 0; padding: 0; background-color: #333; height: 1px;'>",
        unsafe_allow_html=True,
    )

    for idx, prompt in enumerate(prompts):
        col1, col2, col3 = st.columns([1, 20, 3])
        with col1:
            if st.checkbox(
                "Prompt Select",
                key=f"prompt_select_{idx}",
                value=idx in selected_prompts,
                label_visibility="collapsed",
            ):
                if idx not in selected_prompts:
                    selected_prompts.append(idx)
            else:
                if idx in selected_prompts:
                    selected_prompts.remove(idx)

        with col2:
            edited_content = st.text_area(
                "Prompt Content",
                prompt["content"],
                key=f"prompt_content_{idx}",
                label_visibility="collapsed",
                height=150,
            )
            # Update the prompt content if edited
            prompts[idx]["content"] = edited_content

        with col3:
            st.write(prompt["type"].replace("_", " ").title())

        st.markdown(
            "<hr style='margin: 0; padding: 0; background-color: #333; height: 1px;'>",
            unsafe_allow_html=True,
        )


def create_prompts_page():
    if "current_project" not in st.session_state:
        st.switch_page("app.py")
        return

    if "agent_prompt" not in st.session_state:
        st.switch_page("pages/8_create_evaluator_agent_prompt.py")
        return

    if "selected_metrics" not in st.session_state:
        st.switch_page("pages/9_create_evaluator_select_metrics.py")
        return

    if "test_cases" not in st.session_state:
        st.session_state.test_cases = []
    if "selected_prompts" not in st.session_state:
        st.session_state.selected_prompts = []

    api_client = APIClient()
    clear_selected_node_path()
    sidebar = Sidebar(api_client)
    sidebar.render()

    st.title("Create Evaluator - Step 3")
    st.subheader("Create Test Cases")
    st.info(
        "💡 Test cases are LLM generated except in 'Plain Text' where raw input is used. Agent Prompt and User Demographic Info (if provided) are used in generation."
    )

    if st.button(
        "Back to Select Metrics",
        icon=":material/arrow_back:",
        disabled=st.session_state.get("is_generating", False),
    ):
        st.switch_page("pages/9_create_evaluator_select_metrics.py")

    prompt_data = prompt_creation_dialog(api_client)
    if prompt_data:
        st.session_state.test_cases.extend(prompt_data)
        st.session_state.is_generating = False
        st.rerun()

    st.subheader("Current Test Cases")
    display_prompts(st.session_state.test_cases, st.session_state.selected_prompts)

    if st.button(
        "Create Evaluator", disabled=st.session_state.get("is_generating", False)
    ):
        if not st.session_state.selected_prompts:
            st.error("Please select at least one test case")
            return

        final_prompts = []
        for idx in st.session_state.selected_prompts:
            final_prompts.append(st.session_state.test_cases[idx]["content"])

        metric_names = [metric["name"] for metric in st.session_state.selected_metrics]
        response = api_client.post_data(
            evals_ep(st.session_state.current_project),
            {"test_cases": final_prompts, "metric_names": metric_names},
        )

        if response.get("eval_id"):
            st.success("Evaluator created successfully!")
            # Clear session state
            del st.session_state.test_cases
            del st.session_state.selected_prompts
            del st.session_state.agent_prompt
            del st.session_state.selected_metrics
            if "is_generating" in st.session_state:
                del st.session_state.is_generating
            st.switch_page("pages/5_evals_list.py")


if __name__ == "__main__":
    create_prompts_page()
