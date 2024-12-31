import streamlit as st

from mixedvoices.dashboard.api.client import APIClient
from mixedvoices.dashboard.components.sidebar import Sidebar
from mixedvoices.dashboard.components.version_selector import render_version_selector
from mixedvoices.dashboard.visualizations.flow_chart import FlowChart


def view_flow_page():
    if "current_project" not in st.session_state:
        st.switch_page("Home.py")
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
        f"projects/{st.session_state.current_project}/versions/{selected_version}/flow"
    )

    if flow_data.get("steps"):
        flow_chart = FlowChart(flow_data)
        fig = flow_chart.create_figure()
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No flow data available. Add recordings to see the flow visualization.")


if __name__ == "__main__":
    view_flow_page()
