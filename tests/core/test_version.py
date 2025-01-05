from time import sleep

import pytest

import mixedvoices as mv


def check_recording(recording):
    assert recording.is_successful
    assert recording.duration == 10
    assert recording.combined_transcript == "Test transcript"
    assert len(recording.step_ids) == 3
    assert recording.summary == "Test summary"
    assert recording.llm_metrics == {
        "empathy": {"explanation": "This is a test", "score": 5}
    }
    assert recording.call_metrics == {"wpm": 100}
    assert recording.task_status == "COMPLETED"


def test_version(sample_project):
    project = sample_project
    version = project.load_version("v1")
    assert version.recording_count == 2
    assert len(project.list_evaluators()) == 1


def test_add_recording(empty_project, mock_process_recording):
    project = empty_project
    version = project.load_version("v1")
    with pytest.raises(FileNotFoundError):
        version.add_recording("xyz.wav")

    with pytest.raises(ValueError):
        version.add_recording("tests/assets/prompt.txt")

    version.add_recording("tests/assets/call2.wav", is_successful=True)
    for recording in version._recordings.values():
        check_recording(recording)
    version.add_recording("tests/assets/call2.wav", blocking=False, is_successful=True)
    sleep(0.5)
    project = mv.load_project("empty_project")
    version = project.load_version("v1")
    assert version.recording_count == 2
    for recording in version._recordings.values():
        check_recording(recording)

    version = project.create_version("v2", prompt="Testing prompt")

    version.add_recording("tests/assets/call2.wav")

    for recording in version._recordings.values():
        check_recording(recording)
        assert recording.success_explanation == "Test success explanation"
