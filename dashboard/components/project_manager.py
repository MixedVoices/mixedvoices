import html

import streamlit as st

from dashboard.api.client import APIClient
from dashboard.api.endpoints import get_project_versions_endpoint

# Constants
MAX_KEY_LENGTH = 25
LONG_VALUE_THRESHOLD = 50


class ProjectManager:
    def __init__(self, api_client: APIClient, project_id: str):
        self.api_client = api_client
        self.project_id = project_id

    def _reset_form(self):
        """Reset all form-related session state"""
        if "version_name" in st.session_state:
            del st.session_state.version_name
        st.session_state.version_name = ""
        st.session_state.expander_state = True
        st.session_state.metadata_pairs = [{"key": "", "value": ""}]

    def render(self) -> None:
        """Render project management view"""
        st.title(f"Project: {self.project_id}")

        # Initialize states if they don't exist
        if "current_project_id" not in st.session_state:
            st.session_state.current_project_id = self.project_id

        # Initialize version_name if it doesn't exist
        if "version_name" not in st.session_state:
            st.session_state.version_name = ""

        # Check if project has changed after initializing session states
        if st.session_state.current_project_id != self.project_id:
            self._reset_form()
            st.session_state.current_project_id = self.project_id
            st.rerun()

        self._render_version_creation()
        self._render_versions_list()

    def _render_version_creation(self) -> None:
        """Render version creation UI"""
        # Initialize states if they don't exist
        if "expander_state" not in st.session_state:
            st.session_state.expander_state = True
        if "metadata_pairs" not in st.session_state:
            st.session_state.metadata_pairs = [{"key": "", "value": ""}]
        if "version_name" not in st.session_state:
            st.session_state.version_name = ""

        def handle_create_version():
            if not st.session_state.version_name.strip():
                st.error("Please enter a version name")
                return

            # if duplicate keys, st.error
            all_keys = [pair["key"] for pair in st.session_state.metadata_pairs]
            if len(set(all_keys)) != len(all_keys):
                st.error("Duplicate metadata keys are not allowed")
                return

            metadata_dict = {
                pair["key"]: pair["value"]
                for pair in st.session_state.metadata_pairs
                if pair["key"].strip() and len(pair["key"]) <= MAX_KEY_LENGTH
            }

            response = self.api_client.post_data(
                get_project_versions_endpoint(self.project_id),
                {"name": st.session_state.version_name, "metadata": metadata_dict},
            )

            if response.get("message"):
                st.success(response["message"])
                self._reset_form()
                st.rerun()

        with st.expander(
            "Create New Version", expanded=st.session_state.expander_state
        ):
            st.text_input(
                "Version Name", key="version_name", value=st.session_state.version_name
            )

            st.subheader("Metadata")

            to_remove = None

            if st.button("Add Metadata Field"):
                st.session_state.metadata_pairs.append({"key": "", "value": ""})
                st.rerun()

            for i, pair in enumerate(st.session_state.metadata_pairs):
                col1, col2, col3 = st.columns([2, 2, 0.5])

                with col1:
                    key = st.text_input(
                        "Key",
                        value=pair["key"],
                        key=f"key_{i}",
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
                        key=f"value_{i}",
                        placeholder="Enter value",
                        label_visibility="collapsed",
                    )
                    st.session_state.metadata_pairs[i]["value"] = value

                with col3:
                    if i > 0 and st.button("✕", key=f"remove_{i}"):
                        to_remove = i

            if to_remove is not None:
                st.session_state.metadata_pairs.pop(to_remove)
                st.rerun()

            if st.button("Create Version"):
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
