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
from datetime import datetime, timezone

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

def create_interactive_flow(flow_data: Dict, is_recording_flow: bool = False) -> go.Figure:
    """Create an interactive flow visualization with clickable nodes
    
    Args:
        flow_data: Dict containing either:
            - Full flow data with steps, success rates, etc.
            - Recording flow data with simplified steps array
        is_recording_flow: bool indicating if this is a single recording flow
    """
    G = nx.DiGraph()
    
    if is_recording_flow:
        # For recording flow, create a simple linear path
        steps = flow_data.get("steps", [])
        if not steps:
            return go.Figure()  # Return empty figure if no steps
            
        # Add nodes and edges
        for i, step in enumerate(steps):
            G.add_node(step["id"], name=step["name"], data=step)
            if i > 0:  # Connect to previous node
                G.add_edge(steps[i-1]["id"], step["id"])
        
        # Create a simple horizontal layout
        step_count = len(steps)
        total_width = step_count - 1
        pos = {}
        for i, step in enumerate(steps):
            # Center the flow horizontally by subtracting half the total width
            x = i - (total_width / 2)
            pos[step["id"]] = (x, 0)
    else:
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
        node_ids.append(node_data["id"])
        
        if is_recording_flow:
            # For recording flow, use a neutral color and simple hover text
            color = '#4B89DC'  # A pleasant blue
            hover = f"Step: {node_data['name']}"
        else:
            # For full flow, calculate success rate and color
            success_rate = (node_data["number_of_successful_calls"] / node_data["number_of_calls"] * 100 
                          if node_data["number_of_calls"] > 0 else 0)
            color = '#198754' if success_rate >= 80 else '#fd7e14' if success_rate >= 60 else '#dc3545'
            hover = (f"Step: {node_data['name']}<br>"
                    f"Total: {node_data['number_of_calls']}<br>"
                    f"Success: {node_data['number_of_successful_calls']}<br>"
                    f"Rate: {success_rate:.1f}%")
        
        node_colors.append(color)
        node_text.append(node_data["name"])
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

    # # Calculate axis ranges with padding
    # x_min = min(node_x) if node_x else 0
    # x_max = max(node_x) if node_x else 0
    # x_padding = 1
    # y_min = min(node_y) if node_y else 0
    # y_max = max(node_y) if node_y else 0
    # y_padding = 1 if is_recording_flow else 2
    
    # Create figure
    fig = go.Figure(
        data=[edge_trace, node_trace],
        layout=go.Layout(
            showlegend=False,
            hovermode='closest',
            margin=dict(b=5, l=5, r=5, t=5),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(
                showgrid=False, 
                zeroline=False, 
                showticklabels=False,
                # range=[x_min - x_padding, x_max + x_padding]
            ),
            yaxis=dict(
                showgrid=False, 
                zeroline=False, 
                showticklabels=False,
                # range=[y_min - y_padding, y_max + y_padding] if not is_recording_flow else [-1, 1]
            ),
            height=200 if is_recording_flow else 600,  # Smaller height for recording flow
            width=None,  # Allow width to be responsive
            clickmode='event'
        )
    )
    
    return fig
def display_recording_details(recording: Dict, source: str = "main") -> None:
    """Display detailed information about a recording"""
    st.subheader(f"Recording Details: {recording['id']}")
    
    col1, col2 = st.columns(2)
    with col1:
        created_time = datetime.fromtimestamp(
            int(recording["created_at"])
        ).strftime("%-I:%M%p %-d %B %Y")
        st.write("Created:", created_time)
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
                        display_df["created_at"] = display_df["created_at"].dt.strftime("%-I:%M%p %-d %B %Y")
                        
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

            # Initialize session state
            if 'selected_recording_id' not in st.session_state:
                st.session_state.selected_recording_id = None

            # Create DataFrame and format dates
            recordings_df = pd.DataFrame(recordings)
            display_df = recordings_df.copy()
            display_df["created_at"] = pd.to_datetime(display_df["created_at"], unit='s', utc=True)
            display_df["created_at"] = display_df["created_at"].dt.strftime("%-I:%M%p %-d %B %Y")

            # Custom CSS
            st.markdown("""
                <style>
                    .clickable-id {
                        color: #FF4B4B !important;
                        text-decoration: underline;
                        background: none;
                        border: none;
                        padding: 0;
                        cursor: pointer;
                    }
                    .clickable-id:hover {
                        opacity: 0.8;
                    }
                    .stButton button {
                        background: none;
                        border: none;
                        padding: 0;
                        color: #FF4B4B;
                        text-decoration: underline;
                        width: auto !important;
                    }
                    .stButton button:hover {
                        background: none !important;
                        border: none !important;
                        color: #FF4B4B !important;
                        opacity: 0.8;
                    }
                </style>
            """, unsafe_allow_html=True)

            # Recordings table
            st.subheader("All Recordings")
            
            # Table header
            header_cols = st.columns([3, 2, 1, 4])
            with header_cols[0]:
                st.markdown("**Recording ID**")
            with header_cols[1]:
                st.markdown("**Created At**")
            with header_cols[2]:
                st.markdown("**Success**")
            with header_cols[3]:
                st.markdown("**Summary**")
            st.markdown("<hr style='margin: 0; padding: 0; background-color: #333; height: 1px;'>", unsafe_allow_html=True)

            # Table rows
            for idx, row in display_df.iterrows():
                cols = st.columns([3, 2, 1, 4])
                with cols[0]:
                    if st.button(row['id'], key=f"id_btn_{row['id']}", help="Click to view details"):
                        st.session_state.selected_recording_id = row['id']
                with cols[1]:
                    st.write(row['created_at'])
                with cols[2]:
                    st.write("✅" if row['is_successful'] else "❌")
                with cols[3]:
                    st.write(row['summary'] if row['summary'] else "None")
                st.markdown("<hr style='margin: 0; padding: 0; background-color: #333; height: 1px;'>", unsafe_allow_html=True)

            # Show selected recording details
            if st.session_state.selected_recording_id:
                selected_recording = next(
                    (r for r in recordings if r["id"] == st.session_state.selected_recording_id),
                    None
                )
                
                if selected_recording:
                    st.markdown("<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True)
                    st.subheader(f"Recording Details: {selected_recording['id']}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        created_time = datetime.fromtimestamp(
                            int(selected_recording["created_at"]),
                            tz=timezone.utc
                        ).strftime("%-I:%M%p %-d %B %Y")
                        st.write("Created:", created_time)
                        st.write("Status:", "✅ Successful" if selected_recording["is_successful"] else "❌ Failed")
                    with col2:
                        summary = selected_recording.get("summary") or "N/A"
                        st.write("Summary:", summary)
                    
                    # Display flow visualization for this recording
                    st.subheader("Recording Flow")
                    # Fetch flow data for this specific recording
                    recording_flow = fetch_api_data(
                        f"projects/{st.session_state.current_project}/versions/{st.session_state.current_version}"
                        f"/recordings/{selected_recording['id']}/flow"
                    )
                    
                    if recording_flow and recording_flow.get("steps"):
                        fig = create_interactive_flow(recording_flow, is_recording_flow=True)
                        st.plotly_chart(
                            fig,
                            use_container_width=True,
                            config={'displayModeBar': False},
                            key=f"flow_chart_{selected_recording['id']}"
                        )
                    else:
                        st.warning("No flow data available for this recording")

                    # Display transcript
                    if selected_recording.get("combined_transcript"):
                        with st.expander("View Transcript", expanded=False):
                            st.text_area(
                                "Transcript",
                                selected_recording["combined_transcript"],
                                height=200,
                                key=f"transcript_main_{selected_recording['id']}"
                            )

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