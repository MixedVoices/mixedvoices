import streamlit as st

from mixedvoices.dashboard.api.endpoints import project_versions_ep


class VersionCreator:
    def __init__(self, api_client, project_id: str):
        self.api_client = api_client
        self.project_id = project_id
        # Initialize session states
        if "metadata_pairs" not in st.session_state:
            st.session_state.metadata_pairs = [{"key": "", "value": ""}]
        if "form_key" not in st.session_state:
            st.session_state.form_key = 0

    def _reset_form(self):
        """Reset all form-related session state"""
        # Reset metadata pairs to a single empty pair
        st.session_state.metadata_pairs = [{"key": "", "value": ""}]
        # Increment form key to force re-render of inputs
        st.session_state.form_key = st.session_state.get("form_key", 0) + 1
        st.rerun()

    def render_version_form(self) -> None:
        """Render version creation form"""
        with st.expander("Create New Version", icon=":material/add:"):
            # Use form_key in input keys to force fresh renders
            st.text_input(
                "Version Name", key=f"new_version_id_{st.session_state.form_key}"
            )
            st.text_area(
                "Prompt", key=f"new_version_prompt_{st.session_state.form_key}"
            )

            st.subheader("Metadata (Optional)")
            for i, pair in enumerate(st.session_state.metadata_pairs):
                col1, col2 = st.columns(2)
                with col1:
                    key = st.text_input(
                        "Key",
                        value=pair["key"],
                        key=f"meta_key_{i}_{st.session_state.form_key}",
                        placeholder="Enter key",
                    )
                with col2:
                    value = st.text_input(
                        "Value",
                        value=pair["value"],
                        key=f"meta_value_{i}_{st.session_state.form_key}",
                        placeholder="Enter value",
                    )
                st.session_state.metadata_pairs[i] = {"key": key, "value": value}

            if st.button(
                "Add Metadata Field", key=f"add_meta_{st.session_state.form_key}"
            ):
                st.session_state.metadata_pairs.append({"key": "", "value": ""})
                st.rerun()

            if st.button(
                "Create Version", key=f"create_version_{st.session_state.form_key}"
            ):
                self._handle_version_creation()

    def _handle_version_creation(self) -> None:
        """Handle version creation form submission"""
        name = st.session_state[f"new_version_id_{st.session_state.form_key}"]
        prompt = st.session_state[f"new_version_prompt_{st.session_state.form_key}"]

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
            "metadata": metadata or None,
        }

        response = self.api_client.post_data(
            project_versions_ep(self.project_id), payload
        )

        if response.get("message"):
            st.success("Version created successfully!")
            self._reset_form()
        else:
            st.error("Failed to create version")
