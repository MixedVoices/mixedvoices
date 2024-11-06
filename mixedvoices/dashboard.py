# mixedvoices/dashboard.py
import streamlit as st
import pandas as pd
from pathlib import Path
import typer
from typing import Dict, Any, Optional
from mixedvoices.constants import ALL_PROJECTS_FOLDER
import mixedvoices
import sys
import streamlit.web.cli as stcli
import requests
import plotly.express as px
from datetime import datetime

def run_dashboard(port: int = 8501):
    """Run the Streamlit dashboard"""
    # Get the full path to this file
    dashboard_path = Path(__file__).resolve()
    
    # Set up Streamlit command-line args
    sys.argv = [
        "streamlit",
        "run",
        str(dashboard_path),
        "--server.port",
        str(port),
        "--server.address",
        "localhost"
    ]
    
    # Run Streamlit
    sys.exit(stcli.main())

def fetch_api_data(endpoint: str, server_port: int = 8000) -> Dict:
    """Fetch data from the FastAPI backend"""
    try:
        response = requests.get(f"http://localhost:{server_port}/api/{endpoint}")
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        st.error(f"Error fetching data from API: {str(e)}")
        return {}

def post_api_data(endpoint: str, data: Dict, server_port: int = 8000) -> Dict:
    """Post data to the FastAPI backend"""
    try:
        response = requests.post(f"http://localhost:{server_port}/api/{endpoint}", json=data)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        st.error(f"Error posting data to API: {str(e)}")
        return {}

def main():
    """Main Streamlit dashboard"""
    st.set_page_config(
        page_title="MixedVoices Dashboard",
        page_icon="🎙️",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Initialize session state
    if 'current_project' not in st.session_state:
        st.session_state.current_project = None
    if 'current_version' not in st.session_state:
        st.session_state.current_version = None

    # Sidebar
    with st.sidebar:
        st.title("🎙️ MixedVoices")
        
        # Fetch projects
        projects_data = fetch_api_data("projects")
        projects = projects_data.get("projects", [])
        
        # Project selection
        st.session_state.current_project = st.selectbox(
            "Select Project",
            [""] + projects,
            key="project_selector"
        )
        
        # Version selection if project is selected
        if st.session_state.current_project:
            versions_data = fetch_api_data(f"projects/{st.session_state.current_project}/versions")
            versions = versions_data.get("versions", [])
            st.session_state.current_version = st.selectbox(
                "Select Version",
                [""] + [v["name"] for v in versions],
                key="version_selector"
            )
        
        st.divider()
        
        # Create new project
        with st.expander("Create New Project"):
            new_project_name = st.text_input("Project Name")
            if st.button("Create Project"):
                if new_project_name:
                    response = post_api_data(f"projects?name={new_project_name}", {})
                    if response.get("message"):
                        st.success(response["message"])
                        st.rerun()

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
        st.title(f"Project: {st.session_state.current_project}")
        
        # Add new version
        with st.expander("Create New Version"):
            new_version_name = st.text_input("Version Name")
            metadata = st.text_area("Metadata (JSON)", "{}")
            if st.button("Create Version"):
                if new_version_name:
                    response = post_api_data(
                        f"projects/{st.session_state.current_project}/versions",
                        {"name": new_version_name, "metadata": eval(metadata)}
                    )
                    if response.get("message"):
                        st.success(response["message"])
                        st.rerun()
        
        # Display versions
        versions_data = fetch_api_data(f"projects/{st.session_state.current_project}/versions")
        versions = versions_data.get("versions", [])
        
        if versions:
            st.subheader("Versions")
            cols = st.columns(3)
            for i, version in enumerate(versions):
                with cols[i % 3]:
                    st.markdown(f"""
                    #### {version['name']}
                    - Recordings: {version['recording_count']}
                    - Metadata: {version['metadata']}
                    """)
        return

    # Version view
    st.title(f"Version: {st.session_state.current_version}")

    # Fetch version data
    flow_data = fetch_api_data(
        f"projects/{st.session_state.current_project}/versions/{st.session_state.current_version}/flow"
    )
    recordings_data = fetch_api_data(
        f"projects/{st.session_state.current_project}/versions/{st.session_state.current_version}/recordings"
    )

    # Display metrics
    if recordings_data.get("recordings"):
        recordings = recordings_data["recordings"]
        total = len(recordings)
        successful = sum(1 for r in recordings if r["is_successful"])
        success_rate = (successful / total * 100) if total > 0 else 0

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Recordings", total)
        col2.metric("Successful", successful)
        col3.metric("Success Rate", f"{success_rate:.1f}%")

        # Flow visualization
        if flow_data.get("steps"):
            st.subheader("Recording Flow")
            steps_df = pd.DataFrame(flow_data["steps"])
            
            # Calculate success rates for each step
            steps_df["success_rate"] = (
                steps_df["number_of_successful_calls"] / 
                steps_df["number_of_calls"] * 100
            ).fillna(0)

            # Create bar chart
            fig = px.bar(
                steps_df,
                x="name",
                y=["number_of_calls", "number_of_successful_calls"],
                title="Step Statistics",
                barmode="group",
                labels={
                    "name": "Step",
                    "value": "Count",
                    "variable": "Type"
                }
            )
            st.plotly_chart(fig)

        # Recordings table
        st.subheader("Recent Recordings")
        recordings_df = pd.DataFrame(recordings)
        if not recordings_df.empty:
            # Convert timestamp to datetime if needed
            if "created_at" in recordings_df.columns:
                recordings_df["created_at"] = pd.to_datetime(recordings_df["created_at"])
            
            # Display the most recent recordings
            st.dataframe(
                recordings_df[["id", "created_at", "is_successful", "summary"]]
                .sort_values("created_at", ascending=False)
                .head(10)
            )

    # Upload new recording
    with st.expander("Upload Recording"):
        uploaded_file = st.file_uploader("Choose an audio file")
        if uploaded_file and st.button("Upload"):
            files = {"file": uploaded_file}
            response = requests.post(
                f"http://localhost:8000/api/projects/{st.session_state.current_project}/versions/{st.session_state.current_version}/recordings",
                files=files
            )
            if response.status_code == 200:
                st.success("Recording uploaded successfully!")
                st.rerun()
            else:
                st.error("Error uploading recording")

if __name__ == "__main__":
    main()