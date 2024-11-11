import os
import shutil
from unittest.mock import patch

import pytest

import mixedvoices


def get_script(audio_path):
    script_filename = "call1.txt" if "call1" in audio_path else "call2.txt"
    script_path = os.path.join("tests", "assets", script_filename)
    with open(script_path, "r") as f:
        return f.read()


steps1 = [
    "Greeting",
    "Provide Business Information",
    "Determine Call Purpose",
    "Collect Caller Information",
    "Schedule Appointment",
    "Confirm Appointment Details",
    "Farewell",
]
steps2 = [
    "Greeting",
    "Determine Call Purpose",
    "Provide Business Information",
    "Farewell",
]
script1 = get_script("call1.wav")
script2 = get_script("call2.wav")


@pytest.fixture
def temp_project_folder(tmp_path):
    """Create a temporary project folder for testing"""
    test_folder = str(tmp_path / "test_projects")
    os.makedirs(test_folder)

    # Mock the ALL_PROJECTS_FOLDER constant
    with patch("mixedvoices.constants.ALL_PROJECTS_FOLDER", test_folder):
        yield test_folder

    # Cleanup
    shutil.rmtree(test_folder)


@pytest.fixture
def mock_transcribe_and_combine():
    """Mock the process_recording function"""
    with patch("mixedvoices.utils.transcribe_and_combine") as mock:

        def process_side_effect(user_audio_path, assistant_audio_path):
            return get_script(user_audio_path)

        mock.side_effect = process_side_effect

        yield mock


@pytest.fixture
def mock_script_to_step_names():
    """Mock the process_recording function"""
    with patch("mixedvoices.utils.script_to_step_names") as mock:

        def process_side_effect(script, existing_step_names=None):
            if script == script1:
                return steps1
            elif script == script2:
                return steps2

        mock.side_effect = process_side_effect
        yield mock


@pytest.mark.usefixtures("mock_transcribe_and_combine", "mock_script_to_step_names")
def test_core(temp_project_folder):
    call1_path = os.path.join("tests", "assets", "call1.wav")
    call2_path = os.path.join("tests", "assets", "call2.wav")
    script1_path = os.path.join("tests", "assets", "call1.txt")
    p1 = mixedvoices.create_project("p1")

    with pytest.raises(ValueError):
        mixedvoices.create_project("p1")

    v1 = p1.create_version("v1", metadata={"description": "test version"})

    with pytest.raises(ValueError):
        p1.create_version("v1")

    assert set(p1.versions) == {"v1"}
    assert len(v1.recordings) == 0
    assert v1.metadata == {"description": "test version"}

    v1.add_recording(call1_path, blocking=True)
    with pytest.raises(ValueError):
        v1.add_recording(script1_path, blocking=True)
    assert len(v1.recordings) == 1
    assert len(v1.steps) == 7

    p1 = mixedvoices.load_project("p1")
    v1 = p1.load_version("v1")
    assert set(p1.versions) == {"v1"}
    assert len(v1.recordings) == 1
    assert len(v1.steps) == 7
    assert v1.metadata == {"description": "test version"}
    v1.add_recording(call2_path, blocking=True)

    assert len(v1.recordings) == 2
    assert len(v1.steps) == 10

    v2 = p1.create_version("v2")
    assert set(p1.versions) == {"v1", "v2"}
    v2.add_recording(call2_path, blocking=True)
    assert len(v2.recordings) == 1
