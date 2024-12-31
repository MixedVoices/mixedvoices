import streamlit as st


class VersionCreator:
    def __init__(self, api_client, project_id: str):
        self.api_client = api_client
        self.project_id = project_id

        # Initialize session states
        if "version_name" not in st.session_state:
            st.session_state.version_name = ""
        if "prompt" not in st.session_state:
            st.session_state.prompt = ""
        if "success_criteria" not in st.session_state:
            st.session_state.success_criteria = ""
        if "metadata_pairs" not in st.session_state:
            st.session_state.metadata_pairs = [{"key": "", "value": ""}]
        if "show_version_form" not in st.session_state:
            st.session_state.show_version_form = False

    def render_version_form(self) -> None:
        """Render version creation form"""
        with st.form("create_version_form"):
            st.text_input("Version Name", key="new_version_name")
            st.text_area("Prompt", key="new_version_prompt")
            st.text_area("Success Criteria (Optional)", key="new_version_criteria")

            st.subheader("Metadata (Optional)")
            for i, pair in enumerate(st.session_state.metadata_pairs):
                col1, col2 = st.columns(2)
                with col1:
                    key = st.text_input(
                        "Key",
                        value=pair["key"],
                        key=f"meta_key_{i}",
                        placeholder="Enter key",
                    )
                with col2:
                    value = st.text_input(
                        "Value",
                        value=pair["value"],
                        key=f"meta_value_{i}",
                        placeholder="Enter value",
                    )
                st.session_state.metadata_pairs[i] = {"key": key, "value": value}

            if st.form_submit_button("Add Metadata Field"):
                st.session_state.metadata_pairs.append({"key": "", "value": ""})
                st.rerun()

            submitted = st.form_submit_button("Create Version")
            if submitted:
                self._handle_version_creation()

    def _handle_version_creation(self) -> None:
        """Handle version creation form submission"""
        name = st.session_state.new_version_name
        prompt = st.session_state.new_version_prompt

        if not name or not prompt:
            st.error("Please enter both version name and prompt")
            return

        metadata = {
            pair["key"]: pair["value"]
            for pair in st.session_state.metadata_pairs
            if pair["key"].strip() and pair["value"].strip()
        }

        payload = {
            "name": name,
            "prompt": prompt,
            "success_criteria": st.session_state.new_version_criteria or None,
            "metadata": metadata or None,
        }

        response = self.api_client.post_data(
            f"projects/{self.project_id}/versions", payload
        )

        if response.get("message"):
            st.success("Version created successfully!")
            st.session_state.show_version_form = False
            st.session_state.metadata_pairs = [{"key": "", "value": ""}]
            st.rerun()
        else:
            st.error("Failed to create version")
