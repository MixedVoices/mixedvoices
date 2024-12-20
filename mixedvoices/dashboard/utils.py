import streamlit as st


def disable_evaluation_details_page():
    """Apply styles to permanently grey out evaluation page"""
    nav_style = """
    <style>
    /* Target evaluation page specifically */
    div[data-testid="stSidebarNav"] > ul > li:nth-child(6) {
        opacity: 0.4;
        cursor: not-allowed;
        pointer-events: none;
    }
    div[data-testid="stSidebarNav"] > ul > li:nth-child(6):hover {
        opacity: 0.4;
    }
    </style>
    """
    st.markdown(nav_style, unsafe_allow_html=True)


def display_llm_metrics(metrics: dict) -> None:
    """Display LLM metrics in a card-based layout with color coding.

    Args:
        metrics (dict): Dictionary of metrics where each value contains 'score' and 'explanation'
    """
    # Pre-process metrics into pairs for two-column layout
    metric_items = list(metrics.items())
    metric_pairs = [metric_items[i : i + 2] for i in range(0, len(metric_items), 2)]

    # Create metric cards row by row
    for metric_pair in metric_pairs:
        score_cols = st.columns(2)

        for col_idx, (metric, metric_data) in enumerate(metric_pair):
            with score_cols[col_idx]:
                score = metric_data["score"]

                # Format score
                if isinstance(score, (int, float)):
                    formatted_score = f"{score}/10"
                else:
                    formatted_score = str(score)

                # Determine color based on score
                if score == "PASS" or (isinstance(score, (int, float)) and score >= 7):
                    color = "green"
                elif score == "FAIL" or (isinstance(score, (int, float)) and score < 5):
                    color = "red"
                elif score == "NA":
                    color = "gray"
                else:
                    color = "orange"

                # Create score container with visual separation
                st.markdown(
                    f"""
                    <div style="background-color: #1E1E1E; border-radius: 5px; padding: 15px; margin: 5px 0;">
                        <div style="border-bottom: 1px solid #333; padding-bottom: 8px; margin-bottom: 8px;">
                            <strong>{metric}:</strong> <span style='color: {color}'>{formatted_score}</span>
                        </div>
                        <div style="color: #AAAAAA; font-size: 0.9em;">Explanation:</div>
                        <div style="padding: 5px 0;">{metric_data.get('explanation', 'No explanation provided')}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
