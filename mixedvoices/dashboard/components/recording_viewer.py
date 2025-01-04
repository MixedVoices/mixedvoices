from datetime import datetime, timezone

import streamlit as st

from mixedvoices.dashboard.api.client import APIClient
from mixedvoices.dashboard.api.endpoints import recording_flow_ep
from mixedvoices.dashboard.utils import (
    data_to_df_with_dates,
    display_llm_metrics,
    display_llm_metrics_preview,
)
from mixedvoices.dashboard.visualizations.flow_chart import FlowChart


class RecordingViewer:
    def __init__(self, api_client: APIClient, project_id: str, version: str):
        self.api_client = api_client
        self.project_id = project_id
        self.version = version

    def display_recordings_list(self, recordings: list) -> None:
        """Display list of recordings with details"""
        display_df = data_to_df_with_dates(recordings)

        # Table header
        header_cols = st.columns([0.7, 0.7, 0.7, 0.5, 1.5, 2])
        with header_cols[0]:
            st.markdown("**Recording ID**")
        with header_cols[1]:
            st.markdown("**Task Status**")
        with header_cols[2]:
            st.markdown("**Created At**")
        with header_cols[3]:
            st.markdown("**Success**")
        with header_cols[4]:
            st.markdown("**Summary**")
        with header_cols[5]:
            st.markdown("**LLM Metrics**")
        st.markdown(
            "<hr style='margin: 0; padding: 0; background-color: #333; height: 1px;'>",
            unsafe_allow_html=True,
        )

        # Table rows
        for idx, row in display_df.iterrows():
            cols = st.columns([0.7, 0.7, 0.7, 0.5, 1.5, 2])
            with cols[0]:
                recording_id = row["id"][:7] + "..."
                if st.button(
                    recording_id,
                    key=f"id_btn_{row['id']}",
                    help="Click to view details",
                ):
                    self.show_recording_dialog(recordings[idx])
            with cols[1]:
                st.write(row["task_status"])
            with cols[2]:
                st.write(row["created_at"])
            with cols[3]:
                if row["is_successful"] is None:
                    st.write("N/A")
                else:
                    st.write("✅" if row["is_successful"] else "❌")
            with cols[4]:
                st.write(row["summary"] or "None")
            with cols[5]:
                if recordings[idx].get("llm_metrics"):
                    llm_metrics_dict = recordings[idx]["llm_metrics"]
                    display_llm_metrics_preview(llm_metrics_dict)
                else:
                    st.write("No metrics")
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

        created_time = datetime.fromtimestamp(
            int(recording["created_at"]), tz=timezone.utc
        ).strftime("%-I:%M%p %-d %B %Y")
        st.write("Created:", created_time)

        if recording["task_status"] != "COMPLETED":
            st.write("Task Status:", recording["task_status"])

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
        # st.write("Audio Path:", recording["audio_path"])
        if recording["is_successful"] is None:
            st.write("Success:", "N/A")
        else:
            success_value = "✅" if recording["is_successful"] else "❌"
            if recording["success_explanation"]:
                with st.expander(f"Success: {success_value}", expanded=False):
                    st.write("Explanation:", recording["success_explanation"])
            else:
                st.write("Success:", success_value)

        if recording.get("llm_metrics"):
            with st.expander("LLM Metrics", expanded=False):
                display_llm_metrics(recording["llm_metrics"])

        if recording.get("call_metrics"):
            with st.expander("Call Metrics", expanded=False):
                for metric, value in recording["call_metrics"].items():
                    st.write(f"{metric}: {value}")

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
            recording_flow_ep(self.project_id, self.version, recording_id)
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
