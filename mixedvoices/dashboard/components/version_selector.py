from typing import Optional

import streamlit as st

from mixedvoices.dashboard.api.endpoints import project_versions_ep


def render_version_selector(
    api_client, project_id: str, optional: bool = False, show_all: bool = False
) -> Optional[str]:
    """Render version selector with optional all versions view

    Args:
        api_client: API client instance
        project_id: Current project ID
        optional: Whether version selection is optional
        show_all: Whether to show "All Versions" option
    """
    if not project_id:
        if not optional:
            st.warning("Please select a project first")
        return None

    versions_data = api_client.fetch_data(project_versions_ep(project_id))
    versions = versions_data.get("versions", [])

    if not versions:
        if not optional:
            st.warning("No versions found for this project")
        return None

    # Prepare version options
    version_options = ["All Versions"] if show_all else []
    version_options.extend([v["name"] for v in versions])
    if not show_all:
        version_options.insert(0, "")  # Empty option for non-optional selector

    # Determine current index
    if show_all and not st.session_state.current_version:
        current_index = 0  # Select "All Versions" by default
    elif st.session_state.current_version in [v["name"] for v in versions]:
        current_index = version_options.index(st.session_state.current_version)
    else:
        current_index = None

    selected_version = st.selectbox(
        "Select Version",
        version_options,
        index=current_index,
        placeholder="Select a version",
        label_visibility="collapsed",
    )

    # Handle "All Versions" selection
    if selected_version == "All Versions":
        selected_version = None

    if selected_version != st.session_state.current_version:
        st.session_state.current_version = selected_version
        st.rerun()

    return selected_version
