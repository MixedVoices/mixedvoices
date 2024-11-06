# components/recording_viewer.py
from datetime import datetime, timezone
import streamlit as st
import pandas as pd
from api.client import APIClient
from api.endpoints import get_recording_flow_endpoint
from dashboard.visualizations.flow_chart import FlowChart

class RecordingViewer:
    def __init__(self, api_client: APIClient, project_id: str, version: str):
        self.api_client = api_client
        self.project_id = project_id
        self.version = version

    def display_recordings_list(self, recordings: list) -> None:
        """Display list of recordings with details"""
        # Create DataFrame and format dates
        display_df = pd.DataFrame(recordings)
        display_df["created_at"] = pd.to_datetime(display_df["created_at"], unit='s', utc=True)
        display_df["created_at"] = display_df["created_at"].dt.strftime("%-I:%M%p %-d %B %Y")

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
                    self.show_recording_dialog(recordings[idx])
            with cols[1]:
                st.write(row['created_at'])
            with cols[2]:
                st.write("✅" if row['is_successful'] else "❌")
            with cols[3]:
                st.write(row['summary'] if row['summary'] else "None")
            st.markdown("<hr style='margin: 0; padding: 0; background-color: #333; height: 1px;'>", unsafe_allow_html=True)

    @st.dialog("Details", width="large")
    def show_recording_dialog(self, recording: dict) -> None:
        """Show recording details in a dialog"""
        st.subheader(f"Recording ID: {recording['id']}")
        
        col1, col2 = st.columns(2)
        with col1:
            created_time = datetime.fromtimestamp(
                int(recording["created_at"]),
                tz=timezone.utc
            ).strftime("%-I:%M%p %-d %B %Y")
            st.write("Created:", created_time)
            st.write("Status:", "✅ Successful" if recording["is_successful"] else "❌ Failed")
        with col2:
            summary = recording.get("summary") or "N/A"
            st.write("Summary:", summary)
        
        # Display flow visualization for this recording
        st.subheader("Recording Flow")
        self.display_recording_flow(recording['id'])
        
        # Display transcript
        if recording.get("combined_transcript"):
            with st.expander("View Transcript", expanded=False):
                st.text_area(
                    "Transcript",
                    recording["combined_transcript"],
                    height=200,
                    key=f"transcript_dialog_{recording['id']}"
                )

    def display_recording_flow(self, recording_id: str) -> None:
        """Display flow visualization for a recording"""
        recording_flow = self.api_client.fetch_data(
            get_recording_flow_endpoint(self.project_id, self.version, recording_id)
        )
        
        if recording_flow and recording_flow.get("steps"):
            flow_chart = FlowChart(recording_flow, is_recording_flow=True)
            fig = flow_chart.create_figure()
            st.plotly_chart(
                fig,
                use_container_width=True,
                config={'displayModeBar': False},
                key=f"flow_chart_{recording_id}"
            )
        else:
            st.warning("No flow data available for this recording")