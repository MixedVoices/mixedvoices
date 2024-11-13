from datetime import datetime, timezone

import pandas as pd
import streamlit as st
from api.client import APIClient
from api.endpoints import get_recording_flow_endpoint

from mixedvoices.dashboard.visualizations.flow_chart import FlowChart


class RecordingViewer:
    def __init__(self, api_client: APIClient, project_id: str, version: str):
        self.api_client = api_client
        self.project_id = project_id
        self.version = version

    def display_recordings_list(self, recordings: list) -> None:
        """Display list of recordings with details"""
        # Create DataFrame and format dates
        display_df = pd.DataFrame(recordings)
        display_df["created_at"] = pd.to_datetime(
            display_df["created_at"], unit="s", utc=True
        )
        display_df["created_at"] = display_df["created_at"].dt.strftime(
            "%-I:%M%p %-d %B %Y"
        )

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
        st.markdown(
            "<hr style='margin: 0; padding: 0; background-color: #333; height: 1px;'>",
            unsafe_allow_html=True,
        )

        # Table rows
        for idx, row in display_df.iterrows():
            cols = st.columns([3, 2, 1, 4])
            with cols[0]:
                if st.button(
                    row["id"], key=f"id_btn_{row['id']}", help="Click to view details"
                ):
                    self.show_recording_dialog(recordings[idx])
            with cols[1]:
                st.write(row["created_at"])
            with cols[2]:
                if row["is_successful"] is None:
                    st.write("N/A")
                else:
                    st.write("✅" if row["is_successful"] else "❌")
            with cols[3]:
                st.write(row["summary"] or "None")
            st.markdown(
                "<hr style='margin: 0; padding: 0; background-color: #333;"
                " height: 1px;'>",
                unsafe_allow_html=True,
            )

    @st.dialog("Details", width="large")
    def show_recording_dialog(self, recording: dict) -> None:
        """Show recording details in a dialog"""
        st.subheader(f"Recording ID: {recording['id']}")

        audio_path = recording["audio_path"]
        try:
            st.audio(audio_path, format="audio/wav")
        except Exception as e:
            st.error(f"Unable to load audio: {str(e)}")

        st.write("Duration:", f"{round(recording['duration'], 1)} seconds")

        if recording.get("combined_transcript"):
            st.text_area(
                "Transcript",
                recording["combined_transcript"],
                height=200,
                key=f"transcript_dialog_{recording['id']}",
            )

        if recording.get("summary"):
            st.text_area(
                "Summary",
                recording["summary"],
                height=100,
                key=f"summary_dialog_{recording['id']}",
            )
        else:
            st.write("Summary:", "N/A")

        # col1 = st.columns(1)
        # with col1:
        created_time = datetime.fromtimestamp(
            int(recording["created_at"]), tz=timezone.utc
        ).strftime("%-I:%M%p %-d %B %Y")
        st.write("Created:", created_time)
        # st.write("Audio Path:", recording["audio_path"])
        if recording["is_successful"] is None:
            st.write("Status:", "N/A")
        else:
            st.write(
                "Status:",
                "✅ Successful" if recording["is_successful"] else "❌ Failed",
            )
        if recording.get("metadata"):
            source = recording["metadata"].get("source")
            supported_sources = ["vapi"]
            heading = (
                f"{source.capitalize()} Metadata"
                if source in supported_sources
                else "metadata"
            )
            with st.expander(heading, expanded=False):
                # Display top-level simple key-values
                simple_items = {
                    k: v
                    for k, v in recording["metadata"].items()
                    if isinstance(v, (str, int, float, bool))
                }
                if simple_items:
                    st.write("### Basic Information")
                    for key, value in simple_items.items():
                        if key == "source" and value in supported_sources:
                            continue
                        st.write(f"{key}: {value}")

                # Create tabs for nested structures
                complex_items = {
                    k: v
                    for k, v in recording["metadata"].items()
                    if isinstance(v, dict)
                }
                if complex_items:
                    tabs = st.tabs(list(complex_items.keys()))
                    for tab, value in zip(tabs, complex_items.values()):
                        with tab:
                            for sub_key, sub_value in value.items():
                                if isinstance(sub_value, (str, int, float, bool)):
                                    st.write(f"{sub_key}: {sub_value}")
                                else:
                                    st.write(f"{sub_key}:")
                                    st.json(sub_value, expanded=False)

        with st.expander("View Recording Flow", expanded=False):
            self.display_recording_flow(recording["id"])

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
                config={"displayModeBar": False},
                key=f"flow_chart_{recording_id}",
            )
        else:
            st.warning("No flow data available for this recording")
