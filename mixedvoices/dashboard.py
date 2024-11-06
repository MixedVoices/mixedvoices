import streamlit as st
import pandas as pd
from pathlib import Path
import typer
from typing import Dict, Any, Optional
import sys
import streamlit.web.cli as stcli
import requests
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import json
import networkx as nx

def run_dashboard(port: int = 8501):
    """Run the Streamlit dashboard"""
    dashboard_path = Path(__file__).resolve()
    sys.argv = [
        "streamlit",
        "run",
        str(dashboard_path),
        "--server.port",
        str(port),
        "--server.address",
        "localhost"
    ]
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

def create_flow_visualization(flow_data):
    """Create an interactive flow visualization using Plotly"""
    G = nx.DiGraph()
    
    # Add nodes and identify root nodes (nodes with no incoming edges)
    nodes_with_incoming = set()
    for step in flow_data["steps"]:
        G.add_node(step["name"])
        for next_step_id in step["next_step_ids"]:
            next_step = next((s["name"] for s in flow_data["steps"] if s["id"] == next_step_id), None)
            if next_step:
                G.add_edge(step["name"], next_step)
                nodes_with_incoming.add(next_step)
    
    root_nodes = [node for node in G.nodes() if node not in nodes_with_incoming]
    
    # Use hierarchical layout
    pos = nx.spring_layout(G, k=2, iterations=50)
    
    # Adjust y-coordinates to create levels
    levels = {}
    for node in G.nodes():
        # Calculate the longest path from any root to this node
        max_dist = 0
        for root in root_nodes:
            try:
                dist = len(nx.shortest_path(G, root, node)) - 1
                max_dist = max(max_dist, dist)
            except nx.NetworkXNoPath:
                continue
        levels[node] = max_dist
    
    # Normalize positions
    max_level = max(levels.values())
    for node in pos:
        x, _ = pos[node]
        level = levels[node]
        # Reverse the y-coordinate to have flow from top to bottom
        y = 1 - (level / max(1, max_level))
        pos[node] = (x, y)
    
    # Create edge trace
    edge_x = []
    edge_y = []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=1, color='#666'),
        hoverinfo='none',
        mode='lines'
    )

    # Create node trace
    node_x = []
    node_y = []
    node_colors = []
    node_text = []
    hover_text = []
    
    for step in flow_data["steps"]:
        x, y = pos[step["name"]]
        node_x.append(x)
        node_y.append(y)
        
        success_rate = (step["number_of_successful_calls"] / step["number_of_calls"] * 100 
                       if step["number_of_calls"] > 0 else 0)
        
        # Determine node color based on success rate
        color = '#198754' if success_rate >= 80 else '#fd7e14' if success_rate >= 60 else '#dc3545'
        node_colors.append(color)
        
        # Node label
        node_text.append(step["name"])
        
        # Hover text
        hover = (f"Step: {step['name']}<br>"
                f"Total Calls: {step['number_of_calls']}<br>"
                f"Success Rate: {success_rate:.1f}%<br>"
                f"Terminated: {step['number_of_terminated_calls']}")
        hover_text.append(hover)

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        hoverinfo='text',
        text=node_text,
        textposition="bottom center",
        hovertext=hover_text,
        marker=dict(
            showscale=False,
            color=node_colors,
            size=40,
            line_width=2,
            line_color='white'
        )
    )

    # Create figure
    fig = go.Figure(data=[edge_trace, node_trace],
                   layout=go.Layout(
                       showlegend=False,
                       hovermode='closest',
                       margin=dict(b=20,l=5,r=5,t=40),
                       plot_bgcolor='rgba(0,0,0,0)',
                       paper_bgcolor='rgba(0,0,0,0)',
                       xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                       yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                       height=600
                   ))
    
    return fig

def display_recording_details(recording, source="main"):
    """Display detailed information about a recording
    Args:
        recording: The recording data to display
        source: Source identifier to make keys unique ('main' or step ID)
    """
    st.subheader(f"Recording Details: {recording['id']}")
    
    # Basic information
    col1, col2 = st.columns(2)
    with col1:
        st.write("Created:", recording["created_at"])
        st.write("Status:", "✅ Successful" if recording["is_successful"] else "❌ Failed")
    with col2:
        st.write("Steps Traversed:", len(recording["step_ids"]))
    
    # Transcript
    if recording.get("combined_transcript"):
        with st.expander("View Transcript", expanded=True):
            st.text_area(
                "Transcript", 
                recording["combined_transcript"], 
                height=200,
                key=f"transcript_{source}_{recording['id']}"
            )
    
    # Summary
    if recording.get("summary"):
        with st.expander("Call Summary"):
            st.write(recording["summary"])  # Changed to write instead of text_area

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
    if 'selected_step' not in st.session_state:
        st.session_state.selected_step = None

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
                    try:
                        metadata_dict = json.loads(metadata)
                        response = post_api_data(
                            f"projects/{st.session_state.current_project}/versions",
                            {"name": new_version_name, "metadata": metadata_dict}
                        )
                        if response.get("message"):
                            st.success(response["message"])
                            st.rerun()
                    except json.JSONDecodeError:
                        st.error("Invalid JSON in metadata field")
        
        # Display versions
        versions_data = fetch_api_data(f"projects/{st.session_state.current_project}/versions")
        versions = versions_data.get("versions", [])
        
        if versions:
            st.subheader("Versions")
            for i in range(0, len(versions), 3):
                cols = st.columns(3)
                for j, col in enumerate(cols):
                    if i + j < len(versions):
                        version = versions[i + j]
                        with col:
                            st.markdown(f"""
                            #### {version['name']}
                            - Recordings: {version['recording_count']}
                            - Metadata: {version['metadata']}
                            """)
        return

    # Version view
    st.title(f"Version: {st.session_state.current_version}")

    # Create tabs
    tab1, tab2, tab3 = st.tabs(["Flow Analysis", "Recordings", "Upload"])

    # Flow Analysis Tab
    with tab1:
        flow_data = fetch_api_data(
            f"projects/{st.session_state.current_project}/versions/{st.session_state.current_version}/flow"
        )
        
        if flow_data.get("steps"):
            # Interactive flow visualization
            st.subheader("Call Flow Visualization")
            fig = create_flow_visualization(flow_data)
            
            # Display the flow chart
            st.plotly_chart(
                fig, 
                use_container_width=True,
                config={'displayModeBar': False}  # Hide the mode bar for cleaner look
            )
            
            # Step selection dropdown
            st.session_state.selected_step = st.selectbox(
                "Select step to view details",
                options=[step["name"] for step in flow_data["steps"]],
                key="step_selector"
            )
            
            # Step details and recordings
            if st.session_state.selected_step:
                step_data = next((s for s in flow_data["steps"] if s["name"] == st.session_state.selected_step), None)
                if step_data:
                    # Display step metrics
                    st.subheader(f"Step Details: {step_data['name']}")
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
                    recordings = fetch_api_data(
                        f"projects/{st.session_state.current_project}/versions/{st.session_state.current_version}/steps/{step_data['id']}/recordings"
                    )
                    
                    if recordings.get("recordings"):
                        st.subheader("Recordings at this Step")
                        recordings_df = pd.DataFrame(recordings["recordings"])
                        if not recordings_df.empty:
                            # Convert created_at to datetime and then to string for display
                            recordings_df["created_at"] = pd.to_datetime(recordings_df["created_at"])
                            display_df = recordings_df.copy()
                            display_df["created_at"] = display_df["created_at"].dt.strftime("%Y-%m-%d %H:%M:%S")
                            
                            selected_recording = st.data_editor(
                                display_df[["id", "created_at", "is_successful", "summary"]]
                                .sort_values("created_at", ascending=False),
                                use_container_width=True,
                                hide_index=True,
                                column_config={
                                    "created_at": st.column_config.TextColumn("Created At"),
                                    "is_successful": st.column_config.CheckboxColumn("Success"),
                                    "summary": st.column_config.TextColumn("Summary", width="large"),
                                },
                                key=f"step_recordings_{step_data['id']}"
                            )
                            
                            # If a recording is selected, show its details
                            if selected_recording is not None and len(selected_recording) > 0:
                                selected_id = selected_recording.iloc[0]["id"]
                                selected_recording_data = next(
                                    (r for r in recordings["recordings"] if r["id"] == selected_id), 
                                    None
                                )
                                if selected_recording_data:
                                    display_recording_details(selected_recording_data, f"step_{step_data['id']}")

    # Recordings Tab
    with tab2:
        recordings_data = fetch_api_data(
            f"projects/{st.session_state.current_project}/versions/{st.session_state.current_version}/recordings"
        )
        
        if recordings_data.get("recordings"):
            recordings = recordings_data["recordings"]
            
            # Display metrics
            total = len(recordings)
            successful = sum(1 for r in recordings if r["is_successful"])
            success_rate = (successful / total * 100) if total > 0 else 0

            col1, col2, col3 = st.columns(3)
            col1.metric("Total Recordings", total)
            col2.metric("Successful", successful)
            col3.metric("Success Rate", f"{success_rate:.1f}%")

            # Recordings table with selection
            st.subheader("All Recordings")
            recordings_df = pd.DataFrame(recordings)
            if not recordings_df.empty:
                # Convert created_at to datetime and then to string for display
                recordings_df["created_at"] = pd.to_datetime(recordings_df["created_at"])
                display_df = recordings_df.copy()
                display_df["created_at"] = display_df["created_at"].dt.strftime("%Y-%m-%d %H:%M:%S")
                
                selected_recording = st.data_editor(
                    display_df[["id", "created_at", "is_successful", "summary"]]
                    .sort_values("created_at", ascending=False),
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "created_at": st.column_config.TextColumn("Created At"),
                        "is_successful": st.column_config.CheckboxColumn("Success"),
                        "summary": st.column_config.TextColumn("Summary", width="large"),
                    },
                    key="all_recordings"
                )
                
                # If a recording is selected, show its details
                if selected_recording is not None and len(selected_recording) > 0:
                    selected_id = selected_recording.iloc[0]["id"]
                    selected_recording_data = next(
                        (r for r in recordings if r["id"] == selected_id), 
                        None
                    )
                    if selected_recording_data:
                        display_recording_details(selected_recording_data, "main")

    # Upload Tab
    with tab3:
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