import os
import shutil
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

import mixedvoices as mv
from mixedvoices.core.utils import create_steps_from_names

if TYPE_CHECKING:
    from mixedvoices.core.recording import Recording  # pragma: no cover
    from mixedvoices.core.version import Version  # pragma: no cover
from functools import wraps


def needs_api_key(env_var):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not os.getenv(env_var):
                pytest.skip(f"{env_var} not found in environment")
            return func(*args, **kwargs)

        return wrapper

    return decorator


needs_openai_key = needs_api_key("OPENAI_API_KEY")
needs_deepgram_key = needs_api_key("DEEPGRAM_API_KEY")


@pytest.fixture
def mock_base_folder(tmp_path, monkeypatch):
    """Create temporary folder and patch all folder constants."""
    # Create required subdirectories
    (tmp_path / "projects").mkdir()
    (tmp_path / "tasks").mkdir()

    # Patch all constants directly
    monkeypatch.setattr("mixedvoices.constants.MIXEDVOICES_FOLDER", str(tmp_path))
    monkeypatch.setattr(
        "mixedvoices.constants.PROJECTS_FOLDER", str(tmp_path / "projects")
    )
    monkeypatch.setattr("mixedvoices.constants.TASKS_FOLDER", str(tmp_path / "tasks"))
    monkeypatch.setattr(
        "mixedvoices.constants.METRICS_FILE", str(tmp_path / "metrics.json")
    )

    yield tmp_path


@pytest.fixture
def empty_project(mock_base_folder):
    project = mv.create_project("test_project", [])
    project.create_version("v1", prompt="Testing prompt")
    return project


@pytest.fixture
def sample_project(mock_base_folder):
    project_path = os.path.join("tests", "assets", "sample_project")
    shutil.copytree(
        project_path, os.path.join(mock_base_folder, "projects", "sample_project")
    )
    return mv.load_project("sample_project")


@pytest.fixture
def mock_process_recording():
    def side_effect(recording: "Recording", version: "Version", user_channel):
        recording.combined_transcript = "Test transcript"
        recording.duration = 10
        if version.success_criteria and recording.is_successful is None:
            recording.is_successful = True
            recording.success_explanation = "Test success explanation"
        step_names = ["Testing A", "Testing B", "Testing C"]
        all_steps = create_steps_from_names(step_names, version, recording)
        recording.step_ids = [step.step_id for step in all_steps]
        recording.summary = "Test summary"
        recording.llm_metrics = {
            "empathy": {"explanation": "This is a test", "score": 5}
        }
        recording.call_metrics = {"wpm": 100}
        recording.task_status = "COMPLETED"
        recording.save()

    with patch(
        "mixedvoices.core.utils.process_recording", side_effect=side_effect
    ) as mock:
        yield mock
