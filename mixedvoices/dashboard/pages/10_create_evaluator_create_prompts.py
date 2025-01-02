from typing import List

import streamlit as st

from mixedvoices.dashboard.api.client import APIClient
from mixedvoices.dashboard.components.sidebar import Sidebar
from mixedvoices.dashboard.utils import clear_selected_node_path


def generate_prompt(
    api_client, prompt_data: dict, agent_prompt: str, file=None
) -> List[str]:
    generation_data = {
        "agent_prompt": agent_prompt,
        "user_demographic_info": None,
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
        "prompt_generator", files=files, params=generation_data
    )
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
                        "generated_prompts": prompts,
                    }

        with tabs[2]:
            uploaded_file = st.file_uploader(
                "Upload recording file", type=["wav", "mp3"]
            )
            user_channel = st.selectbox("Select user channel", ["left", "right"])
            if st.button("Add Recording Prompt"):
                if uploaded_file:
                    prompts = generate_prompt(
                        api_client,
                        {
                            "type": "recording",
                            "user_channel": user_channel,
                        },
                        st.session_state.agent_prompt,
                        file=uploaded_file,
                    )
                    return {
                        "type": "recording",
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
                        "generated_prompts": prompts,
                    }

    return None


def display_prompts(prompts: List[dict], selected_prompts: List[int]):
    if not prompts:
        st.write("No prompts created yet")
        return

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

    current_idx = 0
    for prompt_group_idx, prompt in enumerate(prompts):
        for gen_prompt in prompt["generated_prompts"]:
            col1, col2, col3 = st.columns([1, 20, 3])
            with col1:
                if st.checkbox(
                    "Prompt Select",
                    key=f"prompt_select_{current_idx}",
                    value=current_idx in selected_prompts,
                    label_visibility="collapsed",
                ):
                    if current_idx not in selected_prompts:
                        selected_prompts.append(current_idx)
                else:
                    if current_idx in selected_prompts:
                        selected_prompts.remove(current_idx)

            with col2:
                st.text_area(
                    "Prompt Content",
                    gen_prompt,
                    key=f"prompt_content_{current_idx}",
                    label_visibility="collapsed",
                    disabled=True,
                    height=150,
                )

            with col3:
                st.write(prompt["type"].replace("_", " ").title())

            current_idx += 1

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

    if "eval_prompts" not in st.session_state:
        st.session_state.eval_prompts = []
    if "selected_prompts" not in st.session_state:
        st.session_state.selected_prompts = []

    api_client = APIClient()
    clear_selected_node_path()
    sidebar = Sidebar(api_client)
    sidebar.render()

    st.title("Create Evaluator - Step 3")
    st.subheader("Create Prompts")

    if st.button("← Back to Select Metrics"):
        st.switch_page("pages/9_create_evaluator_select_metrics.py")

    prompt_data = prompt_creation_dialog(api_client)
    if prompt_data:
        st.session_state.eval_prompts.append(prompt_data)
        st.rerun()

    st.subheader("Created Prompts")
    display_prompts(st.session_state.eval_prompts, st.session_state.selected_prompts)

    if st.button("Create Evaluator"):
        if not st.session_state.selected_prompts:
            st.error("Please select at least one prompt")
            return

        final_prompts = []
        for idx in st.session_state.selected_prompts:
            current_prompt_group = st.session_state.eval_prompts[idx]
            final_prompts.extend(current_prompt_group["generated_prompts"])

        response = api_client.post_data(
            f"projects/{st.session_state.current_project}/evals",
            {
                "eval_prompts": final_prompts,
                "metric_names": st.session_state.selected_metrics,
            },
        )

        if response.get("eval_id"):
            st.success("Evaluator created successfully!")
            # Clear session state
            del st.session_state.eval_prompts
            del st.session_state.selected_prompts
            del st.session_state.agent_prompt
            del st.session_state.selected_metrics
            st.switch_page("pages/5_evals_list.py")


if __name__ == "__main__":
    create_prompts_page()
