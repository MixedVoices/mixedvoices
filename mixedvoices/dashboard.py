import streamlit as st
import pandas as pd
from pathlib import Path
import typer
from typing import Dict, Any, Optional, List
import sys
import streamlit.web.cli as stcli
import requests
import plotly.graph_objects as go
import json
import networkx as nx
from datetime import datetime

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

def create_interactive_flow(flow_data: Dict) -> go.Figure:
    """Create an interactive flow visualization with clickable nodes"""
    G = nx.DiGraph()
    
    # Track parent-child relationships for proper layout
    parent_child = {}
    for step in flow_data["steps"]:
        G.add_node(step["id"], name=step["name"], data=step)
        for next_step_id in step["next_step_ids"]:
            G.add_edge(step["id"], next_step_id)
            if next_step_id not in parent_child:
                parent_child[next_step_id] = []
            parent_child[next_step_id].append(step["id"])
    
    # Find root nodes (nodes with no parents)
    root_nodes = [node for node in G.nodes() if node not in parent_child]
    
    # Assign levels using BFS
    levels = {node: -1 for node in G.nodes()}
    current_level = 0
    current_nodes = root_nodes
    while current_nodes:
        next_nodes = []
        for node in current_nodes:
            if levels[node] == -1:  # Not visited yet
                levels[node] = current_level
                next_nodes.extend(list(G.successors(node)))
        current_nodes = next_nodes
        current_level += 1
    
    # Position nodes
    max_level = max(levels.values())
    nodes_by_level = {}
    for node, level in levels.items():
        if level not in nodes_by_level:
            nodes_by_level[level] = []
        nodes_by_level[level].append(node)
    
    # Calculate positions with straight-line layout for paths
    pos = {}
    for level in range(max_level + 1):
        nodes = nodes_by_level[level]
        
        # Special handling for branching paths
        if len(nodes) == 1:
            # For single nodes, maintain the x-position of their parent if possible
            node = nodes[0]
            parent_nodes = parent_child.get(node, [])
            if parent_nodes and parent_nodes[0] in pos:
                pos[node] = (pos[parent_nodes[0]][0], -level)
            else:
                pos[node] = (0, -level)
        else:
            # For multiple nodes at the same level, space them evenly
            total_width = len(nodes) - 1
            for i, node in enumerate(sorted(nodes)):
                x = i - total_width/2
                pos[node] = (x, -level)
    
    # Create edge trace
    edge_x, edge_y = [], []
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
    node_x, node_y = [], []
    node_text, hover_text = [], []
    node_ids = []
    node_colors = []
    
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        
        node_data = G.nodes[node]['data']
        node_ids.append(node)
        
        success_rate = (node_data["number_of_successful_calls"] / node_data["number_of_calls"] * 100 
                       if node_data["number_of_calls"] > 0 else 0)
        
        color = '#198754' if success_rate >= 80 else '#fd7e14' if success_rate >= 60 else '#dc3545'
        node_colors.append(color)
        
        node_text.append(node_data["name"])
        
        hover = (f"Step: {node_data['name']}<br>"
                f"Total: {node_data['number_of_calls']}<br>"
                f"Success: {node_data['number_of_successful_calls']}<br>"
                f"Rate: {success_rate:.1f}%")
        hover_text.append(hover)
    
    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        hoverinfo='text',
        text=node_text,
        textposition="bottom center",
        hovertext=hover_text,
        customdata=node_ids,  # Store node IDs for click events
        marker=dict(
            showscale=False,
            color=node_colors,
            size=40,
            line_width=2,
            line_color='white'
        )
    )
    
    # Create figure with clickable nodes
    fig = go.Figure(
        data=[edge_trace, node_trace],
        layout=go.Layout(
            showlegend=False,
            hovermode='closest',
            margin=dict(b=20, l=5, r=5, t=40),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            height=600,
            clickmode='event'  # Enable click events
        )
    )
    
    return fig

def display_recording_details(recording: Dict, source: str = "main") -> None:
    """Display detailed information about a recording"""
    st.subheader(f"Recording Details: {recording['id']}")
    
    col1, col2 = st.columns(2)
    with col1:
        st.write("Created:", recording["created_at"])
        st.write("Status:", "✅ Successful" if recording["is_successful"] else "❌ Failed")
    with col2:
        st.write("Steps Traversed:", len(recording["step_ids"]))
    
    if recording.get("combined_transcript"):
        with st.expander("View Transcript", expanded=True):
            st.text_area(
                "Transcript",
                recording["combined_transcript"],
                height=200,
                key=f"transcript_{source}_{recording['id']}"
            )
    
    if recording.get("summary"):
        with st.expander("Call Summary"):
            st.write(recording["summary"])

def handle_node_click(flow_data: Dict, selected_point: Dict, fetch_api_data) -> None:
    """Handle node click events and display relevant information"""
    if selected_point and selected_point.get("points"):
        point = selected_point["points"][0]
        node_id = point.get("customdata")
        if node_id:
            step_data = next((s for s in flow_data["steps"] if s["id"] == node_id), None)
            if step_data:
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
                    f"projects/{st.session_state.current_project}"
                    f"/versions/{st.session_state.current_version}"
                    f"/steps/{node_id}/recordings"
                )
                
                if recordings.get("recordings"):
                    st.subheader("Recordings at this Step")
                    recordings_df = pd.DataFrame(recordings["recordings"])
                    if not recordings_df.empty:
                        recordings_df["created_at"] = pd.to_datetime(recordings_df["created_at"])
                        display_df = recordings_df.copy()
                        display_df["created_at"] = display_df["created_at"].dt.strftime("%Y-%m-%d %H:%M:%S")
                        
                        selected_indices = st.data_editor(
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
                        
                        if selected_indices:
                            selected_recording = recordings["recordings"][selected_indices[0]]
                            display_recording_details(selected_recording, f"step_{node_id}")

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
            st.subheader("Call Flow Visualization")
            fig = create_interactive_flow(flow_data)
            
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
            if selected_point is not None:  # Check if selected_point exists
                with details_placeholder:
                    if isinstance(selected_point, dict) and "points" in selected_point:
                        handle_node_click(flow_data, selected_point, fetch_api_data)

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
                
                selected_indices = st.data_editor(
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
                ).index.tolist()
                
                # If a recording is selected, show its details
                if selected_indices:
                    selected_recording = recordings[selected_indices[0]]
                    display_recording_details(selected_recording, "main")

    # Upload Tab
    with tab3:
        st.subheader("Upload Recording")
        uploaded_file = st.file_uploader("Choose an audio file")
        if uploaded_file and st.button("Upload"):
            files = {"file": uploaded_file}
            try:
                response = requests.post(
                    f"http://localhost:8000/api/projects/{st.session_state.current_project}"
                    f"/versions/{st.session_state.current_version}/recordings",
                    files=files
                )
                response.raise_for_status()
                st.success("Recording uploaded successfully!")
                st.rerun()
            except requests.RequestException as e:
                st.error(f"Error uploading recording: {str(e)}")

def cli():
    """Command line interface function"""
    typer.run(run_dashboard)

if __name__ == "__main__":
    main()