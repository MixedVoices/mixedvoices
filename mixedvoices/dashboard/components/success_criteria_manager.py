import streamlit as st


class SuccessCriteriaManager:
    def __init__(self, api_client, project_id: str):
        self.api_client = api_client
        self.project_id = project_id

    def _render_edit_form(self, current_criteria: str) -> None:
        """Renders the edit form for success criteria"""
        new_criteria = st.text_area(
            "Success Criteria",
            value=current_criteria,
            height=150,
            key="success_criteria_editor",
        )

        cols = st.columns([1, 4])
        with cols[0]:
            if st.button("Save", icon=":material/check:"):
                response = self.api_client.post_data(
                    f"projects/{self.project_id}/success_criteria",
                    {"success_criteria": new_criteria},
                )
                if response.get("message"):
                    st.session_state.success_message = "Success criteria updated!"
                    st.session_state.is_editing_success_criteria = False
                    st.rerun()
        with cols[1]:
            if st.button("Cancel", icon=":material/close:"):
                st.session_state.is_editing_success_criteria = False
                st.rerun()

    def render(self) -> None:
        """Renders the success criteria section"""
        st.markdown("#### Current Success Criteria")

        if "is_editing_success_criteria" not in st.session_state:
            st.session_state.is_editing_success_criteria = False

        # Show success message if exists and clear it
        if "success_message" in st.session_state:
            st.success(st.session_state.success_message)
            del st.session_state.success_message

        success_criteria = self.api_client.fetch_data(
            f"projects/{self.project_id}/success_criteria"
        ).get("success_criteria", "")

        if st.session_state.is_editing_success_criteria:
            self._render_edit_form(success_criteria)
        else:
            if success_criteria:
                st.write(success_criteria)
                button_text = "Edit Success Criteria"
            else:
                st.warning("Success criteria hasn't been defined")
                button_text = "Set Success Criteria"

            if st.button(button_text, icon=":material/edit:"):
                st.session_state.is_editing_success_criteria = True
                st.rerun()
