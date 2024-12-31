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


def display_llm_metrics_preview(llm_metrics_dict: dict):
    score_cols = st.columns(2)
    for i, (metric, score_data) in enumerate(llm_metrics_dict.items()):
        with score_cols[i % 2]:
            score = score_data["score"]
            if isinstance(score, (int, float)):
                formatted_score = f"{score}/10"
            else:
                formatted_score = str(score)

            if score == "PASS" or (isinstance(score, (int, float)) and score >= 7):
                color = "green"
            elif score == "FAIL" or (isinstance(score, (int, float)) and score < 5):
                color = "red"
            elif score == "NA":
                color = "gray"
            else:
                color = "orange"

            st.markdown(
                f"**{metric}:** <span style='color: {color}'>{formatted_score}</span>",
                unsafe_allow_html=True,
            )


def clear_selected_node_path():
    st.session_state.selected_node_id = None
    st.session_state.selected_path = None


def apply_nav_styles():
    """Apply minimal styles to the navigation"""
    has_project = bool(st.session_state.get("current_project"))

    nav_style = """
        <style>
            section[data-testid="stSidebar"] > div:first-child {
                width: 350px;
            }
            
            section[data-testid="stSidebar"] a:not([href*="Home.py"]) {
                opacity: %s;
                pointer-events: %s;
                position: relative;
            }
            
            section[data-testid="stSidebar"] a:not([href*="Home.py"]):hover::after {
                content: "Select project first";
                position: absolute;
                left: 100%%;
                margin-left: 10px;
                background: rgba(0, 0, 0, 0.8);
                color: white;
                padding: 5px 10px;
                border-radius: 4px;
                font-size: 12px;
                white-space: nowrap;
                z-index: 1000;
                display: %s;
            }
        </style>
    """ % (
        "1" if has_project else "0.4",  # opacity
        "auto" if has_project else "none",  # pointer-events
        "none" if has_project else "block",  # tooltip display
    )
    st.markdown(nav_style, unsafe_allow_html=True)
