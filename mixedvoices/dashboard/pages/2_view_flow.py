import streamlit as st
from streamlit_plotly_events import plotly_events

from mixedvoices.dashboard.api.client import APIClient
from mixedvoices.dashboard.api.endpoints import version_flow_ep
from mixedvoices.dashboard.components.sidebar import Sidebar
from mixedvoices.dashboard.components.version_selector import render_version_selector
from mixedvoices.dashboard.visualizations.flow_chart import FlowChart


def get_path_to_node(flow_data: dict, target_node_id: str) -> list:
    """Calculate path to node using previous_node_id"""
    nodes_map = {step["id"]: step for step in flow_data["steps"]}
    path = []
    current_node_id = target_node_id
    while current_node_id:
        current_node = nodes_map.get(current_node_id)
        if current_node:
            path.append(current_node["name"])
            current_node_id = current_node.get("previous_step_id")
        else:
            break
    return list(reversed(path))


def view_flow_page():
    if "current_project" not in st.session_state:
        st.switch_page("app.py")
        return

    api_client = APIClient()
    sidebar = Sidebar(api_client)
    sidebar.render()

    st.title("Call Flow Visualization")

    # Version selection required
    selected_version = render_version_selector(
        api_client, st.session_state.current_project
    )
    if not selected_version:
        return

    # Fetch flow data
    flow_data = api_client.fetch_data(
        version_flow_ep(st.session_state.current_project, selected_version)
    )

    if flow_data.get("steps"):
        st.info(
            "💡 This is step wise breakdown of your voice agent's calls. Click on a node to view calls that followed that path"
        )
        flow_chart = FlowChart(flow_data)
        fig = flow_chart.create_figure()

        # Store node list in state to maintain order
        nodes = list(flow_chart.G.nodes())
        st.session_state.flow_nodes = nodes

        # Handle click events using plotly_events
        clicked = plotly_events(
            fig, click_event=True, override_height=600, key="flow_chart"
        )

        if clicked and len(clicked) > 0:
            point_data = clicked[0]
            curve_number = point_data.get("curveNumber")
            point_number = point_data.get("pointNumber")

            # Only process node clicks (curveNumber 1 is for nodes, 0 is for edges)
            # Get the node ID using the point number as index into our stored nodes list
            if (
                curve_number == 1
                and point_number is not None
                and point_number < len(nodes)
            ):
                node_id = nodes[point_number]
                path = get_path_to_node(flow_data, node_id)

                # Update session state
                st.session_state.selected_node_id = node_id
                st.session_state.selected_path = " -> ".join(path)

                # Directly switch to recordings page
                st.switch_page("pages/3_view_recordings.py")
    else:
        st.warning(
            "No flow data available. Add recordings to see the flow visualization."
        )


if __name__ == "__main__":
    view_flow_page()
