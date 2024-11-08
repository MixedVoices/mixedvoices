from typing import Dict, List

import streamlit as st


def display_metrics(recordings: List[Dict]) -> None:
    """Display recording metrics"""
    total = len(recordings)
    successful = sum(1 for r in recordings if r["is_successful"])
    success_rate = (successful / total * 100) if total > 0 else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Recordings", total)
    col2.metric("Successful", successful)
    col3.metric("Success Rate", f"{success_rate:.1f}%")
