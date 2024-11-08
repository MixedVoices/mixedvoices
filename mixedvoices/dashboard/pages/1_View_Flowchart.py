import streamlit as st
from streamlit_plotly_events import plotly_events

from mixedvoices.dashboard.api.client import APIClient
from mixedvoices.dashboard.api.endpoints import get_version_flow_endpoint
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


def flow_page():
    if (
        "current_project" not in st.session_state
        or "current_version" not in st.session_state
    ):
        st.switch_page("Home.py")
        return

    st.title(f"{st.session_state.current_project} | {st.session_state.current_version}")

    # Initialize API client
    api_client = APIClient()

    flow_data = api_client.fetch_data(
        get_version_flow_endpoint(
            st.session_state.current_project, st.session_state.current_version
        )
    )

    if flow_data.get("steps"):
        st.subheader("Call Flow Visualization")

        # Create flow chart
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
                st.switch_page("pages/2_View_Recordings.py")
    else:
        st.info(
            "No recordings found for this version."
            " Upload recordings using the Upload tab or using Python API."
        )


if __name__ == "__main__":
    flow_page()
