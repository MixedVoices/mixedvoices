from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import requests
import streamlit as st
from streamlit.testing.v1 import AppTest

from mixedvoices.dashboard import utils
from mixedvoices.dashboard.api.client import APIClient
from mixedvoices.dashboard.components.evaluation_viewer import EvaluationViewer
from mixedvoices.dashboard.components.project_manager import ProjectManager
from mixedvoices.dashboard.components.recording_viewer import RecordingViewer
from mixedvoices.dashboard.components.sidebar import Sidebar
from mixedvoices.dashboard.components.upload_form import UploadForm
from mixedvoices.dashboard.visualizations.flow_chart import FlowChart
from mixedvoices.dashboard.visualizations.metrics import display_metrics

# Get the root directory of the project
ROOT_DIR = Path(__file__).parent.parent.parent


# Fixtures
@pytest.fixture
def app_home():
    """Create a Streamlit AppTest instance for Home.py"""
    app = AppTest(str(ROOT_DIR / "mixedvoices/dashboard/Home.py"), default_timeout=10)
    st.session_state["current_page"] = "home"
    return app


@pytest.fixture
def app_flowchart():
    """Create a Streamlit AppTest instance for View_Flowchart.py"""
    app = AppTest(
        str(ROOT_DIR / "mixedvoices/dashboard/pages/1_View_Flowchart.py"),
        default_timeout=10,
    )
    st.session_state["current_page"] = "flowchart"
    return app


@pytest.fixture
def app_recordings():
    """Create a Streamlit AppTest instance for View_Recordings.py"""
    app = AppTest(
        str(ROOT_DIR / "mixedvoices/dashboard/pages/2_View_Recordings.py"),
        default_timeout=10,
    )
    st.session_state["current_page"] = "recordings"
    return app


@pytest.fixture
def app_upload():
    """Create a Streamlit AppTest instance for Upload_Recordings.py"""
    app = AppTest(
        str(ROOT_DIR / "mixedvoices/dashboard/pages/3_Upload_Recordings.py"),
        default_timeout=10,
    )
    st.session_state["current_page"] = "upload"
    return app


@pytest.fixture
def app_evaluations():
    """Create a Streamlit AppTest instance for View_Evaluations.py"""
    app = AppTest(
        str(ROOT_DIR / "mixedvoices/dashboard/pages/4_View_Evaluations.py"),
        default_timeout=10,
    )
    st.session_state["current_page"] = "evaluations"
    return app


@pytest.fixture
def mock_api_client():
    return MagicMock(spec=APIClient)


@pytest.fixture
def sample_flow_data():
    return {
        "steps": [
            {
                "id": "1",
                "name": "Start",
                "next_step_ids": ["2"],
                "number_of_calls": 10,
                "number_of_failed_calls": 2,
            },
            {
                "id": "2",
                "name": "Process",
                "next_step_ids": ["3"],
                "number_of_calls": 8,
                "number_of_failed_calls": 1,
            },
            {
                "id": "3",
                "name": "End",
                "next_step_ids": [],
                "number_of_calls": 7,
                "number_of_failed_calls": 0,
            },
        ]
    }


# Test API Client
class TestAPIClient:
    def test_handle_request_error_connection_error(self):
        """Test handling of connection errors"""
        error = requests.ConnectionError()
        with patch.object(st, "error") as mock_error:
            APIClient.handle_request_error(error, "fetch")
            mock_error.assert_called_once()
            assert "Failed to connect to API server" in mock_error.call_args[0][0]

    def test_handle_request_error_timeout(self):
        """Test handling of timeout errors"""
        error = requests.Timeout()
        with patch.object(st, "error") as mock_error:
            APIClient.handle_request_error(error, "fetch")
            mock_error.assert_called_once()
            assert "Request timed out" in mock_error.call_args[0][0]

    def test_fetch_data_success(self):
        """Test successful data fetching"""
        with patch("requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = {"data": "test"}
            mock_get.return_value = mock_response
            mock_response.raise_for_status.return_value = None

            result = APIClient.fetch_data("test/endpoint")
            assert result == {"data": "test"}


# Test Sidebar Component
class TestSidebar:
    def test_render(self, app_home, mock_api_client):
        """Test sidebar rendering"""
        # Setup mock API response for projects
        mock_api_client.fetch_data.side_effect = [
            {"projects": ["project1", "project2"]},  # First call for projects
            {"versions": [{"name": "v1"}, {"name": "v2"}]},  # Second call for versions
        ]

        # Initialize session state
        st.session_state["current_project"] = None
        st.session_state["current_version"] = None

        # Create a real Sidebar instance with our mock client
        sidebar = Sidebar(mock_api_client)

        # Patch streamlit components that Sidebar uses
        with patch("streamlit.title") as mock_title, patch(
            "streamlit.selectbox"
        ) as mock_selectbox, patch("streamlit.divider") as mock_divider, patch(
            "streamlit.expander"
        ) as mock_expander:

            sidebar.render()

            # Verify the sidebar components were called
            mock_title.assert_called_with("🎙️ MixedVoices")
            mock_selectbox.assert_any_call(
                "Select Project",
                [""] + ["project1", "project2"],
                key="project_selector",
            )
            mock_divider.assert_called_once()
            mock_expander.assert_called_with("Create New Project")


# Test Upload Form Component
class TestUploadForm:
    def test_render_initial_state(self, app_upload, mock_api_client):
        """Test initial render of upload form"""
        # Initialize session state
        st.session_state["current_project"] = "test_project"
        st.session_state["current_version"] = "v1"
        st.session_state["is_uploading"] = False
        st.session_state["form_key"] = 0
        st.session_state["show_success"] = False

        upload_form = UploadForm(mock_api_client, "test_project", "v1")
        with patch("streamlit.subheader") as mock_subheader:
            upload_form.render()
            mock_subheader.assert_called_with("Upload Recording")

    def test_upload_success(self, app_upload, mock_api_client):
        """Test successful file upload"""
        st.session_state.current_project = "test_project"
        st.session_state.current_version = "v1"
        st.session_state.is_uploading = True
        st.session_state.form_key = 0
        st.session_state.show_success = False

        mock_api_client.post_data.return_value = {"status": "success"}

        upload_form = UploadForm(mock_api_client, "test_project", "v1")

        with patch("streamlit.file_uploader", return_value=MagicMock()), patch(
            "streamlit.info"
        ) as mock_info:
            upload_form.render()
            mock_info.assert_called_with("Upload in progress...", icon="🔄")


# Test Project Manager Component
class TestProjectManager:
    def test_render_initial_state(self, mock_api_client):
        """Test initial render of project manager"""
        with patch("streamlit.title") as mock_title:
            manager = ProjectManager(mock_api_client, "test_project")
            manager.render()
            mock_title.assert_called_with("Project: test_project")


# Test Recording Viewer Component
class TestRecordingViewer:
    def test_display_recordings_list(self, mock_api_client):
        """Test display of recordings list"""
        with patch("streamlit.write") as mock_write:
            recordings = [
                {
                    "id": "rec1",
                    "task_status": "COMPLETED",
                    "created_at": 1609459200,
                    "is_successful": True,
                    "summary": "Test recording",
                }
            ]

            viewer = RecordingViewer(mock_api_client, "test_project", "v1")
            viewer.display_recordings_list(recordings)

            # Verify header was written
            mock_write.assert_any_call("## Recordings")


# Test Evaluation Viewer Component
class TestEvaluationViewer:
    def test_display_evaluations_list(self, app_evaluations, mock_api_client):
        """Test evaluations list display"""
        evaluations = [{"eval_id": "eval1", "created_at": 1609459200}]

        st.session_state.current_project = "test_project"
        st.session_state.current_version = "v1"

        viewer = EvaluationViewer(mock_api_client, "test_project", "v1")
        with patch("streamlit.write") as mock_write:
            viewer.display_evaluations_list(evaluations)
            mock_write.assert_any_call("## Evaluations")


# Test Flow Chart Component
class TestFlowChart:
    def test_create_recording_graph(self, sample_flow_data):
        """Test creation of recording flow graph"""
        chart = FlowChart(sample_flow_data, is_recording_flow=True)
        chart._create_recording_graph()
        assert len(chart.G.nodes()) == 3
        assert len(chart.G.edges()) == 2

    def test_create_full_graph(self, sample_flow_data):
        """Test creation of full flow graph"""
        chart = FlowChart(sample_flow_data)
        chart._create_full_graph()
        assert len(chart.G.nodes()) == 3
        assert len(chart.G.edges()) == 2
        assert len(chart.tree_roots) == 1

    def test_create_figure(self, sample_flow_data):
        """Test figure creation"""
        chart = FlowChart(sample_flow_data)
        fig = chart.create_figure()
        assert len(fig.data) == 2  # Edge trace and node trace


# Test Utils
class TestUtils:
    def test_display_llm_metrics(self, app_home):
        """Test display of LLM metrics"""
        with patch("streamlit.markdown") as mock_markdown:
            metrics = {
                "metric1": {"score": 8, "explanation": "Good"},
                "metric2": {"score": "PASS", "explanation": "Passed"},
            }
            utils.display_llm_metrics(metrics)
            mock_markdown.assert_called()


# Test CLI
class TestCLI:
    def test_run_dashboard(self, monkeypatch):
        """Test dashboard run function"""
        from mixedvoices.dashboard.cli import run_dashboard

        mock_argv = [
            "streamlit",
            "run",
            str(ROOT_DIR / "mixedvoices/dashboard/Home.py"),
            "--server.port",
            "7761",
            "--server.address",
            "localhost",
        ]
        mock_exit = MagicMock()
        mock_main = MagicMock()

        monkeypatch.setattr("sys.argv", mock_argv)
        monkeypatch.setattr("sys.exit", mock_exit)
        monkeypatch.setattr("streamlit.web.cli.main", mock_main)

        run_dashboard(7761)
        mock_main.assert_called_once()


# Test Home Page
def test_home_page_initial_state(app_home):
    """Test initial state of home page"""
    st.session_state["current_project"] = None
    st.session_state["current_version"] = None
    st.session_state["current_page"] = "home"

    app_home.run()

    # Verify welcome message is displayed
    titles = [element.value for element in app_home.title]
    assert "Welcome to MixedVoices" in titles


def test_display_metrics():
    # Test with empty list
    with patch("streamlit.columns") as mock_cols:
        # Test with sample recordings
        recordings = [
            {"is_successful": True},
            {"is_successful": False},
            {"is_successful": True},
        ]

        col1, col2, col3 = MagicMock(), MagicMock(), MagicMock()
        mock_cols.return_value = col1, col2, col3
        display_metrics(recordings)

        # Verify metrics
        col1.metric.assert_called_with("Total Recordings", 3)
        col2.metric.assert_called_with("Successful", 2)
        col3.metric.assert_called_with("Success Rate", "66.7%")


if __name__ == "__main__":
    pytest.main(["-v"])
