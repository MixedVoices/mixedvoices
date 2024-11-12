import html

import streamlit as st

from mixedvoices.dashboard.api.client import APIClient
from mixedvoices.dashboard.api.endpoints import get_project_versions_endpoint

# Constants
MAX_KEY_LENGTH = 25
LONG_VALUE_THRESHOLD = 50


class ProjectManager:
    def __init__(self, api_client: APIClient, project_id: str):
        self.api_client = api_client
        self.project_id = project_id

    def _reset_form(self):
        """Reset all form-related session state"""
        # Reset version name
        st.session_state.version_name = ""

        # Reset metadata pairs to a single empty pair
        st.session_state.metadata_pairs = [{"key": "", "value": ""}]

        # Reset form key to force re-render of inputs
        st.session_state.form_key = st.session_state.get("form_key", 0) + 1

        # Keep expander open
        st.session_state.expander_state = True

        # Clear any error messages
        if "version_error" in st.session_state:
            del st.session_state.version_error

    def render(self) -> None:
        """Render project management view"""
        st.title(f"Project: {self.project_id}")

        # Initialize states if they don't exist
        if "current_project_id" not in st.session_state:
            st.session_state.current_project_id = self.project_id
        if "version_name" not in st.session_state:
            st.session_state.version_name = ""
        if "form_key" not in st.session_state:
            st.session_state.form_key = 0
        if "show_version_success" not in st.session_state:
            st.session_state.show_version_success = False

        # Check if project has changed
        if st.session_state.current_project_id != self.project_id:
            self._reset_form()
            st.session_state.current_project_id = self.project_id
            st.rerun()

        # Show success message if needed
        if st.session_state.show_version_success:
            st.success("Version created successfully!")
            st.session_state.show_version_success = False

        self._render_version_creation()
        self._render_versions_list()

    def _render_version_creation(self) -> None:
        """Render version creation UI"""
        # Initialize states if they don't exist
        if "expander_state" not in st.session_state:
            st.session_state.expander_state = True
        if "metadata_pairs" not in st.session_state:
            st.session_state.metadata_pairs = [{"key": "", "value": ""}]

        def handle_version_name_change():
            """Callback for version name input change"""
            if "version_error" in st.session_state:
                del st.session_state.version_error

        def handle_create_version():
            current_version_name = st.session_state.get(
                f"version_name_{st.session_state.form_key}", ""
            ).strip()

            if not current_version_name:
                st.session_state.version_error = "Please enter a version name"
                return

            # Check for duplicate keys
            filled_keys = [
                pair["key"]
                for pair in st.session_state.metadata_pairs
                if pair["key"].strip()
            ]
            if len(set(filled_keys)) != len(filled_keys):
                st.session_state.version_error = (
                    "Duplicate metadata keys are not allowed"
                )
                return

            metadata_dict = {
                pair["key"]: pair["value"]
                for pair in st.session_state.metadata_pairs
                if pair["key"].strip() and len(pair["key"]) <= MAX_KEY_LENGTH
            }

            response = self.api_client.post_data(
                get_project_versions_endpoint(self.project_id),
                {"name": current_version_name, "metadata": metadata_dict},
            )

            if response.get("message"):
                st.session_state.show_version_success = True
                self._reset_form()
                st.rerun()

        with st.expander(
            "Create New Version", expanded=st.session_state.expander_state
        ):
            version_name_key = f"version_name_{st.session_state.form_key}"
            st.text_input(
                "Version Name",
                key=version_name_key,
                on_change=handle_version_name_change,
            )

            # Display error if exists
            if "version_error" in st.session_state:
                st.error(st.session_state.version_error)

            st.subheader("Metadata")

            to_remove = None

            if st.button(
                "Add Metadata Field", key=f"add_metadata_{st.session_state.form_key}"
            ):
                st.session_state.metadata_pairs.append({"key": "", "value": ""})
                st.rerun()

            for i, pair in enumerate(st.session_state.metadata_pairs):
                col1, col2, col3 = st.columns([2, 2, 0.5])

                with col1:
                    key = st.text_input(
                        "Key",
                        value=pair["key"],
                        key=f"key_{i}_{st.session_state.form_key}",
                        placeholder="Enter key",
                        max_chars=MAX_KEY_LENGTH,
                        label_visibility="collapsed",
                    )
                    st.session_state.metadata_pairs[i]["key"] = key
                    if len(key) > MAX_KEY_LENGTH:
                        st.error(f"Key must be {MAX_KEY_LENGTH} characters or less")

                with col2:
                    value = st.text_input(
                        "Value",
                        value=pair["value"],
                        key=f"value_{i}_{st.session_state.form_key}",
                        placeholder="Enter value",
                        label_visibility="collapsed",
                    )
                    st.session_state.metadata_pairs[i]["value"] = value

                with col3:
                    if i > 0 and st.button(
                        "✕", key=f"remove_{i}_{st.session_state.form_key}"
                    ):
                        to_remove = i

            if to_remove is not None:
                st.session_state.metadata_pairs.pop(to_remove)
                st.rerun()

            if st.button(
                "Create Version", key=f"create_version_{st.session_state.form_key}"
            ):
                handle_create_version()

    def _render_versions_list(self) -> None:
        """Render list of versions"""
        versions_data = self.api_client.fetch_data(
            get_project_versions_endpoint(self.project_id)
        )
        versions = versions_data.get("versions", [])

        if versions:
            st.subheader("Versions")
            versions.sort(key=lambda x: x["name"].lower())

            st.markdown(
                """
                <style>
                    .version-card {
                        background-color: #1E1E1E;
                        border: 1px solid #333;
                        border-radius: 8px;
                        padding: 1rem;
                        margin-bottom: 1rem;
                        min-height: 120px;
                    }
                    .version-header {
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        margin-bottom: 0.5rem;
                        padding-bottom: 0.5rem;
                        border-bottom: 1px solid #333;
                    }
                    .version-name {
                        font-size: 1.2rem;
                        font-weight: bold;
                        color: #FFFFFF;
                    }
                    .recording-count {
                        color: #B0B0B0;
                        font-size: 0.9rem;
                    }
                    .metadata-section {
                        margin-top: 0.5rem;
                    }
                    .metadata-item {
                        display: grid;
                        grid-template-columns: minmax(80px, auto) 1fr;
                        gap: 1rem;
                        padding: 0.2rem 0;
                        align-items: start;
                    }
                    .metadata-key {
                        color: #888;
                        min-width: fit-content;
                        padding-right: 0.5rem;
                    }
                    .metadata-value {
                        color: #B0B0B0;
                    }
                    .metadata-textarea {
                        background-color: #2A2A2A;
                        border: 1px solid #333;
                        border-radius: 4px;
                        padding: 0.5rem;
                        color: #B0B0B0;
                        width: 100%;
                        min-height: 60px;
                        resize: vertical;
                    }
                    .no-metadata {
                        color: #666;
                        font-style: italic;
                        text-align: center;
                        padding: 1rem 0;
                    }
                </style>
            """,
                unsafe_allow_html=True,
            )

            for i in range(0, len(versions), 3):
                cols = st.columns(3)
                for j, col in enumerate(cols):
                    if i + j < len(versions):
                        version = versions[i + j]
                        with col:
                            metadata_content = ""
                            if version["metadata"]:
                                metadata_items = []
                                for key, value in version["metadata"].items():
                                    safe_key = html.escape(str(key))
                                    safe_value = html.escape(str(value))

                                    # Use textarea for long values
                                    if len(str(value)) > LONG_VALUE_THRESHOLD:
                                        value_html = (
                                            "<textarea class="
                                            f'"metadata-textarea" readonly>{safe_value}'
                                            "</textarea>"
                                        )
                                    else:
                                        value_html = (
                                            '<span class="metadata-value">'
                                            f"{safe_value}</span>"
                                        )

                                    metadata_items.append(
                                        f'<div class="metadata-item">'
                                        f'<span class="metadata-key">{safe_key}:</span>'
                                        f"{value_html}"
                                        f"</div>"
                                    )
                                metadata_content = "".join(metadata_items)
                            else:
                                metadata_content = (
                                    '<div class="no-metadata">No metadata</div>'
                                )
                            version_name = html.escape(version["name"])
                            n = version["recording_count"]
                            card_html = f"""
                            <div class="version-card">
                                <div class="version-header">
                                    <span class="version-name">{version_name}</span>
                                    <span class="recording-count">Recordings: {n}</span>
                                </div>
                                <div class="metadata-section">
                                    {metadata_content}
                                </div>
                            </div>
                            """
                            st.markdown(card_html, unsafe_allow_html=True)
