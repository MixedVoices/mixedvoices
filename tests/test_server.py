import os
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from mixedvoices.server.server import app

client = TestClient(app)


@pytest.fixture
def mock_projects_folder(tmp_path):
    with patch("mixedvoices.constants.ALL_PROJECTS_FOLDER", str(tmp_path)):
        yield tmp_path


def test_list_projects_empty(mock_projects_folder):
    response = client.get("/api/projects")
    assert response.status_code == 200
    assert response.json() == {"projects": []}


def test_create_and_list_project(mock_projects_folder):
    # Create project
    response = client.post("/api/projects", params={"name": "test_project"})
    assert response.status_code == 200
    assert response.json() == {"message": "Project test_project created successfully"}

    # List projects
    response = client.get("/api/projects")
    assert response.status_code == 200
    assert response.json() == {"projects": ["test_project"]}


def test_create_duplicate_project(mock_projects_folder):
    # Create project first time
    response = client.post("/api/projects", params={"name": "test_project"})
    assert response.status_code == 200

    # Try to create same project again
    response = client.post("/api/projects", params={"name": "test_project"})
    assert response.status_code == 400


def test_list_versions_nonexistent_project(mock_projects_folder):
    response = client.get("/api/projects/nonexistent/versions")
    assert response.status_code == 404


def test_create_and_list_versions(mock_projects_folder):
    # Create project first
    client.post("/api/projects", params={"name": "test_project"})

    # Create version
    version_data = {"name": "v1", "metadata": {"description": "test version"}}
    response = client.post("/api/projects/test_project/versions", json=version_data)
    assert response.status_code == 200

    # List versions
    response = client.get("/api/projects/test_project/versions")
    assert response.status_code == 200
    versions = response.json()["versions"]
    assert len(versions) == 1
    assert versions[0]["name"] == "v1"
    assert versions[0]["metadata"] == {"description": "test version"}


def test_add_recording(mock_projects_folder):
    # Create project and version first
    client.post("/api/projects", params={"name": "test_project"})
    version_data = {"name": "v1", "metadata": {"description": "test version"}}
    client.post("/api/projects/test_project/versions", json=version_data)

    # Create a temporary audio file
    test_audio_path = mock_projects_folder / "test_audio.wav"
    test_audio_path.write_bytes(b"fake audio data")

    # Upload recording
    with open(test_audio_path, "rb") as f:
        response = client.post(
            "/api/projects/test_project/versions/v1/recordings",
            files={"file": ("test_audio.wav", f, "audio/wav")},
        )

    assert response.status_code == 200
    assert "recording_id" in response.json()

    # Cleanup temp file
    test_audio_path.unlink()


def test_get_version_flow(mock_projects_folder):
    # Create project and version
    client.post("/api/projects", params={"name": "test_project"})
    version_data = {"name": "v1", "metadata": {"description": "test version"}}
    client.post("/api/projects/test_project/versions", json=version_data)

    # Get flow data
    response = client.get("/api/projects/test_project/versions/v1/flow")
    assert response.status_code == 200
    assert "steps" in response.json()


def test_get_recordings(mock_projects_folder):
    # Create project and version
    client.post("/api/projects", params={"name": "test_project"})
    version_data = {"name": "v1", "metadata": {"description": "test version"}}
    client.post("/api/projects/test_project/versions", json=version_data)

    # List recordings (should be empty initially)
    response = client.get("/api/projects/test_project/versions/v1/recordings")
    assert response.status_code == 200
    assert response.json() == {"recordings": []}


def test_get_step_recordings(mock_projects_folder):
    # Create project and version
    client.post("/api/projects", params={"name": "test_project"})
    version_data = {"name": "v1", "metadata": {"description": "test version"}}
    client.post("/api/projects/test_project/versions", json=version_data)

    # Get recordings for a step (should be empty initially)
    response = client.get(
        "/api/projects/test_project/versions/v1/steps/step1/recordings"
    )
    assert response.status_code == 404  # Since step doesn't exist yet


# Add teardown to clean temporary files
def teardown_module(module):
    # Clean up any remaining temporary files
    if os.path.exists("/tmp"):
        for file in os.listdir("/tmp"):
            if file.startswith("test_") and file.endswith(".wav"):
                os.remove(os.path.join("/tmp", file))
