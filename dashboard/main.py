# main.py
import streamlit as st
from dashboard.api.client import APIClient
from dashboard.api.endpoints import (
    get_version_flow_endpoint,
    get_version_recordings_endpoint,
    get_step_recordings_endpoint
)
from dashboard.components.sidebar import Sidebar
from dashboard.components.project_manager import ProjectManager
from dashboard.components.recording_viewer import RecordingViewer
from dashboard.components.upload_form import UploadForm
from dashboard.visualizations.flow_chart import FlowChart
from dashboard.visualizations.metrics import display_metrics
from dashboard.config import DEFAULT_PAGE_CONFIG
import pandas as pd

def initialize_session_state():
    """Initialize session state variables"""
    if 'current_project' not in st.session_state:
        st.session_state.current_project = None
    if 'current_version' not in st.session_state:
        st.session_state.current_version = None

def handle_node_click(api_client: APIClient, flow_data: dict, selected_point: dict,
                     project_id: str, version: str, recording_viewer: RecordingViewer) -> None:
    """Handle node click events in the flow visualization"""
    if selected_point and selected_point.get("points"):
        point = selected_point["points"][0]
        node_id = point.get("customdata")
        if node_id:
            step_data = next((s for s in flow_data["steps"] if s["id"] == node_id), None)
            if step_data:
                st.subheader(f"Step Details: {step_data['name']}")
                
                # Display metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Calls", step_data["number_of_calls"])
                with col2:
                    st.metric("Successful Calls", step_data["number_of_successful_calls"])
                with col3:
                    success_rate = (step_data["number_of_successful_calls"] / 
                                step_data["number_of_calls"] * 100 if step_data["number_of_calls"] > 0 else 0)
                    st.metric("Success Rate", f"{success_rate:.1f}%")
                
                # Fetch and display recordings for this step
                recordings = api_client.fetch_data(
                    get_step_recordings_endpoint(project_id, version, node_id)
                )
                
                if recordings.get("recordings"):
                    st.subheader("Recordings at this Step")
                    recordings_df = pd.DataFrame(recordings["recordings"])
                    if not recordings_df.empty:
                        selected_indices = display_recordings_table(recordings_df, node_id)
                        if selected_indices:
                            selected_recording = recordings["recordings"][selected_indices[0]]
                            recording_viewer.display_recording_details(
                                selected_recording,
                                f"step_{node_id}"
                            )

def display_recordings_table(recordings_df: pd.DataFrame, node_id: str) -> list:
    """Display recordings table with formatting"""
    recordings_df["created_at"] = pd.to_datetime(recordings_df["created_at"], unit='s')
    display_df = recordings_df.copy()
    display_df["created_at"] = display_df["created_at"].dt.strftime("%-I:%M%p %-d %B %Y")
    
    return st.data_editor(
        display_df[["id", "created_at", "is_successful", "summary"]]
        .sort_values("created_at", ascending=False),
        use_container_width=True,
        hide_index=True,
        column_config={
            "created_at": st.column_config.TextColumn("Created At"),
            "is_successful": st.column_config.CheckboxColumn("Success"),
            "summary": st.column_config.TextColumn("Summary", width="large"),
        },
        key=f"recordings_table_{node_id}"
    ).index.tolist()

def main():
    """Main application"""
    # Set page config
    st.set_page_config(**DEFAULT_PAGE_CONFIG)
    
    # Initialize session state
    initialize_session_state()
    
    # Initialize API client
    api_client = APIClient()
    
    # Render sidebar
    sidebar = Sidebar(api_client)
    sidebar.render()
    
    # Main content
    if not st.session_state.current_project:
        st.title("Welcome to MixedVoices")
        st.markdown("""
        ### Getting Started
        1. Select or create a project using the sidebar
        2. Add versions to track changes
        3. Upload recordings to analyze
        """)
        return
    
    # Project view
    if not st.session_state.current_version:
        project_manager = ProjectManager(api_client, st.session_state.current_project)
        project_manager.render()
        return
    
    # Version view
    st.title(f"Version: {st.session_state.current_version}")
    
    # Initialize components
    recording_viewer = RecordingViewer(
        api_client,
        st.session_state.current_project,
        st.session_state.current_version
    )
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["Flow Analysis", "Recordings", "Upload"])
    
    # Flow Analysis Tab
    with tab1:
        flow_data = api_client.fetch_data(
            get_version_flow_endpoint(
                st.session_state.current_project,
                st.session_state.current_version
            )
        )
        
        if flow_data.get("steps"):
            st.subheader("Call Flow Visualization")
            flow_chart = FlowChart(flow_data)
            fig = flow_chart.create_figure()
            
            # Create a placeholder for selected node details
            details_placeholder = st.empty()
            
            # Display the interactive flow chart
            selected_point = st.plotly_chart(
                fig,
                use_container_width=True,
                config={'displayModeBar': False},
                key="flow_chart"
            )
            
            # Handle node click events
            if selected_point is not None:
                with details_placeholder:
                    if isinstance(selected_point, dict) and "points" in selected_point:
                        handle_node_click(
                            api_client,
                            flow_data,
                            selected_point,
                            st.session_state.current_project,
                            st.session_state.current_version,
                            recording_viewer
                        )
    
    with tab2:
        recordings_data = api_client.fetch_data(
            get_version_recordings_endpoint(
                st.session_state.current_project,
                st.session_state.current_version
            )
        )
        
        if recordings_data.get("recordings"):
            recordings = recordings_data["recordings"]
            
            # Display metrics
            display_metrics(recordings)
            
            # Display recordings list
            recording_viewer.display_recordings_list(recordings)
        else:
            st.info("No recordings found for this version. Upload recordings using the Upload tab.")
    
    # Upload Tab
    with tab3:
        upload_form = UploadForm(
            api_client,
            st.session_state.current_project,
            st.session_state.current_version
        )
        upload_form.render()

if __name__ == "__main__":
    main()