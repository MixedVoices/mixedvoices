import shutil
import tempfile
from typing import List

import streamlit as st

from mixedvoices.dashboard.api.client import APIClient
from mixedvoices.dashboard.components.metrics_manager import MetricsManager
from mixedvoices.dashboard.components.sidebar import Sidebar
from mixedvoices.dashboard.utils import clear_selected_node_path


def generate_prompt(api_client, prompt_data: dict, agent_prompt: str) -> List[str]:
    generation_data = {
        "agent_prompt": agent_prompt,
        "user_demographic_info": None,
        "transcript": None,
        "recording_file": None,
        "user_channel": None,
        "description": None,
        "edge_case_count": None,
    }

    if prompt_data["type"] == "plain_text":
        return [prompt_data["content"]]

    if prompt_data["type"] == "transcript":
        generation_data["transcript"] = prompt_data["content"]
    elif prompt_data["type"] == "recording":
        generation_data["recording_file"] = prompt_data["file_path"]
        generation_data["user_channel"] = prompt_data["user_channel"]
    elif prompt_data["type"] == "edge_cases":
        generation_data["edge_case_count"] = prompt_data["count"]
    elif prompt_data["type"] == "description":
        generation_data["description"] = prompt_data["content"]

    print("Posting data", generation_data)
    response = api_client.post_data("prompt_generator", generation_data)
    return response.get("prompts", [])


def prompt_creation_dialog(api_client):
    with st.expander("Create New Prompt", expanded=True):
        tabs = st.tabs(
            ["Plain Text", "Transcript", "Recording", "Edge Cases", "Description"]
        )

        with tabs[0]:
            prompt = st.text_area("Enter your prompt")
            if st.button("Add Plain Text Prompt"):
                if prompt:
                    return {
                        "type": "plain_text",
                        "content": prompt,
                        "generated_prompts": [prompt],
                    }

        with tabs[1]:
            transcript = st.text_area("Enter the transcript")
            if st.button("Add Transcript Prompt"):
                if transcript:
                    prompts = generate_prompt(
                        api_client,
                        {"type": "transcript", "content": transcript},
                        st.session_state.agent_prompt,
                    )
                    return {
                        "type": "transcript",
                        "content": transcript,
                        "generated_prompts": prompts,
                    }

        with tabs[2]:
            uploaded_file = st.file_uploader(
                "Upload recording file", type=["wav", "mp3"]
            )
            user_channel = st.selectbox("Select user channel", ["left", "right"])
            if st.button("Add Recording Prompt"):
                if uploaded_file:
                    with tempfile.NamedTemporaryFile(
                        delete=False, suffix=".wav"
                    ) as tmp_file:
                        shutil.copyfileobj(uploaded_file, tmp_file)
                        prompts = generate_prompt(
                            api_client,
                            {
                                "type": "recording",
                                "file_path": tmp_file.name,
                                "user_channel": user_channel,
                            },
                            st.session_state.agent_prompt,
                        )
                        return {
                            "type": "recording",
                            "file": uploaded_file,
                            "user_channel": user_channel,
                            "file_path": tmp_file.name,
                            "generated_prompts": prompts,
                        }

        with tabs[3]:
            count = st.number_input("Number of edge cases", min_value=1, value=1)
            if st.button("Add Edge Cases"):
                prompts = generate_prompt(
                    api_client,
                    {"type": "edge_cases", "count": count},
                    st.session_state.agent_prompt,
                )
                return {
                    "type": "edge_cases",
                    "count": count,
                    "generated_prompts": prompts,
                }

        with tabs[4]:
            description = st.text_area("Enter description")
            if st.button("Add Description Prompt"):
                if description:
                    prompts = generate_prompt(
                        api_client,
                        {"type": "description", "content": description},
                        st.session_state.agent_prompt,
                    )
                    return {
                        "type": "description",
                        "content": description,
                        "generated_prompts": prompts,
                    }

    return None


def display_prompts(prompts: List[dict], selected_prompts: List[int]):
    if not prompts:
        st.write("No prompts created yet")
        return

    col1, col2, col3 = st.columns([1, 3, 2])
    with col1:
        st.write("Select")
    with col2:
        st.write("Prompt")
    with col3:
        st.write("Created From")

    for i, prompt in enumerate(prompts):
        col1, col2, col3 = st.columns([1, 3, 2])
        with col1:
            if st.checkbox("", key=f"prompt_select_{i}", value=i in selected_prompts):
                if i not in selected_prompts:
                    selected_prompts.append(i)
            else:
                if i in selected_prompts:
                    selected_prompts.remove(i)

        with col2:
            if prompt["type"] in ["plain_text", "transcript", "description"]:
                st.text_area(
                    "",
                    prompt["content"],
                    key=f"prompt_content_{i}",
                    label_visibility="collapsed",
                    disabled=True,
                )
                with st.expander("Generated Prompts"):
                    for gen_prompt in prompt["generated_prompts"]:
                        st.write(gen_prompt)
            elif prompt["type"] == "recording":
                st.write(f"Recording: {prompt['file'].name}")
                with st.expander("Generated Prompts"):
                    for gen_prompt in prompt["generated_prompts"]:
                        st.write(gen_prompt)
            elif prompt["type"] == "edge_cases":
                st.write(f"Edge cases: {prompt['count']}")
                with st.expander("Generated Prompts"):
                    for gen_prompt in prompt["generated_prompts"]:
                        st.write(gen_prompt)

        with col3:
            st.write(prompt["type"].replace("_", " ").title())


def create_evaluator_page():
    if "current_project" not in st.session_state:
        st.switch_page("app.py")
        return

    api_client = APIClient()
    clear_selected_node_path()
    sidebar = Sidebar(api_client)
    sidebar.render()

    if "eval_step" not in st.session_state:
        st.session_state.eval_step = 1
    if "eval_prompts" not in st.session_state:
        st.session_state.eval_prompts = []
    if "selected_prompts" not in st.session_state:
        st.session_state.selected_prompts = []
    if "agent_prompt" not in st.session_state:
        st.session_state.agent_prompt = ""

    st.title("Create Evaluator")

    if st.session_state.eval_step == 1:
        st.subheader("Step 1: Agent Prompt")
        st.session_state.agent_prompt = st.text_area(
            "Enter agent prompt", st.session_state.agent_prompt
        )

        if st.button("Next"):
            if not st.session_state.agent_prompt.strip():
                st.error("Please enter an agent prompt")
            else:
                st.session_state.eval_step = 2
                st.rerun()

    elif st.session_state.eval_step == 2:
        st.subheader("Step 2: Create Prompts")

        if st.button("Back"):
            st.session_state.eval_step = 1
            st.rerun()

        prompt_data = prompt_creation_dialog(api_client)
        if prompt_data:
            st.session_state.eval_prompts.append(prompt_data)
            st.rerun()

        st.divider()
        st.subheader("Created Prompts")
        display_prompts(
            st.session_state.eval_prompts, st.session_state.selected_prompts
        )

        if st.button("Next"):
            if not st.session_state.selected_prompts:
                st.error("Please select at least one prompt")
            else:
                st.session_state.eval_step = 3
                st.rerun()

    elif st.session_state.eval_step == 3:
        st.subheader("Step 3: Select Metrics")

        if st.button("Back"):
            st.session_state.eval_step = 2
            st.rerun()

        metrics_manager = MetricsManager(api_client, st.session_state.current_project)
        selected_metrics = metrics_manager.render(selection_mode=True)

        if st.button("Create Evaluator"):
            if not selected_metrics:
                st.error("Please select at least one metric")
                return

            final_prompts = []
            for idx in st.session_state.selected_prompts:
                final_prompts.extend(
                    st.session_state.eval_prompts[idx]["generated_prompts"]
                )

            response = api_client.post_data(
                f"projects/{st.session_state.current_project}/evals",
                {"eval_prompts": final_prompts, "metric_names": selected_metrics},
            )

            if response.get("eval_id"):
                st.success("Evaluator created successfully!")
                st.session_state.eval_step = 1
                st.session_state.eval_prompts = []
                st.session_state.selected_prompts = []
                st.session_state.agent_prompt = ""
                st.rerun()


if __name__ == "__main__":
    create_evaluator_page()
