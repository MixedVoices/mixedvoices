from fastapi.testclient import TestClient

from mixedvoices.server.server import app

client = TestClient(app)

# TODO: Add test for vapi


def test_create_and_list_project(mock_base_folder):
    # Create project
    response = client.post("/api/projects", params={"name": "test_project"})
    assert response.status_code == 200
    assert response.json() == {"message": "Project test_project created successfully"}

    # Create another project with white space in name
    response = client.post("/api/projects", params={"name": "test project"})
    assert response.status_code == 400

    # Create another project with same name
    response = client.post("/api/projects", params={"name": "test_project"})
    assert response.status_code == 400

    # List projects
    response = client.get("/api/projects")
    assert response.status_code == 200
    assert response.json() == {"projects": ["test_project"]}


def test_create_and_list_version(mock_base_folder):
    # Create project first
    client.post("/api/projects", params={"name": "test_project"})

    # Create version
    version_data = {
        "name": "v1",
        "prompt": "Testing prompt",
        "metadata": {"description": "test"},
        "success_criteria": "Testing success criteria",
    }
    response = client.post("/api/projects/test_project/versions", json=version_data)
    assert response.status_code == 200

    # Create another version with white space in name
    version_data = {"name": "v 1", "prompt": "Testing prompt"}
    response = client.post("/api/projects/test_project/versions", json=version_data)
    assert response.status_code == 400

    # Create another version with same name
    response = client.post("/api/projects/test_project/versions", json=version_data)
    assert response.status_code == 400

    # List versions
    response = client.get("/api/projects/test_project/versions")
    assert response.status_code == 200
    versions = response.json()["versions"]
    assert len(versions) == 1
    assert versions[0]["name"] == "v1"
    assert versions[0]["prompt"] == "Testing prompt"
    assert versions[0]["metadata"] == {"description": "test"}
    assert versions[0]["success_criteria"] == "Testing success criteria"
    assert versions[0]["recording_count"] == 0


def test_create_and_list_recording(mock_base_folder, mock_process_recording):
    # Create project and version first
    client.post("/api/projects", params={"name": "test_project"})
    version_data = {"name": "v1", "prompt": "Testing prompt"}
    client.post("/api/projects/test_project/versions", json=version_data)

    # List recordings (should be empty initially)
    response = client.get("/api/projects/test_project/versions/v1/recordings")
    assert response.status_code == 200
    assert response.json() == {"recordings": []}

    audio_path = "tests/assets/call2.wav"

    # Upload recording
    with open(audio_path, "rb") as f:
        response = client.post(
            "/api/projects/test_project/versions/v1/recordings",
            files={"file": ("call2.wav", f, "audio/wav")},
        )

    assert response.status_code == 200
    assert "recording_id" in response.json()

    # List recordings
    response = client.get("/api/projects/test_project/versions/v1/recordings")
    assert response.status_code == 200
    recordings = response.json()["recordings"]
    assert len(recordings) == 1
    assert recordings[0]["audio_path"].endswith("call2.wav")

    # list recordings of a project that does not exist
    response = client.get("/api/projects/nonexistent/versions/v1/recordings")
    assert response.status_code == 404


def test_list_and_get_flow_of_recordings(sample_project):
    response = client.get("/api/projects/sample_project/versions/v1/flow")
    assert response.status_code == 200
    assert "steps" in response.json()
    step_names = [step["name"] for step in response.json()["steps"]]
    step_ids = [step["id"] for step in response.json()["steps"]]
    assert set(step_names) == {
        "Caller Complaint Handling",
        "Farewell",
        "Greeting",
        "Inquiry Handling",
        "Offer Further Assistance",
        "Set Appointment",
    }

    # get version flow of a version that does not exist
    response = client.get("/api/projects/sample_project/versions/v2/flow")
    assert response.status_code == 404

    # get all recordings
    response = client.get("/api/projects/sample_project/versions/v1/recordings")
    assert response.status_code == 200
    assert len(response.json()["recordings"]) == 2

    recording_ids = [recording["id"] for recording in response.json()["recordings"]]

    for recording_id in recording_ids:
        # get flow of the recording
        response = client.get(
            f"/api/projects/sample_project/versions/v1/recordings/{recording_id}/flow"
        )
        assert response.status_code == 200
        assert "steps" in response.json()
        assert len(response.json()["steps"]) > 0

    # get flow of a recording that does not exist
    response = client.get(
        "/api/projects/sample_project/versions/v1/recordings/nonexistent/flow"
    )
    assert response.status_code == 404

    # list step recordings for all step_ids
    for step_id in step_ids:
        response = client.get(
            f"/api/projects/sample_project/versions/v1/steps/{step_id}/recordings"
        )
        assert response.status_code == 200
        assert "recordings" in response.json()
        assert len(response.json()["recordings"]) in {1, 2}

    # list step recordings for a step_id that does not exist
    response = client.get(
        "/api/projects/sample_project/versions/v1/steps/nonexistent/recordings"
    )
    assert response.status_code == 404


def test_list_evals(sample_project):
    response = client.get("/api/projects/sample_project/versions/v1/evals")
    assert response.status_code == 200
    assert "evals" in response.json()
    assert len(response.json()["evals"]) == 1

    eval_id = response.json()["evals"][0]["eval_id"]

    # list evals of a version that does not exist
    response = client.get("/api/projects/sample_project/versions/v2/evals")
    assert response.status_code == 404

    # get eval details
    response = client.get(f"/api/projects/sample_project/versions/v1/evals/{eval_id}")
    assert response.status_code == 200
    assert "agents" in response.json()
    assert len(response.json()["agents"]) == 3

    # get eval details of an eval that does not exist
    response = client.get("/api/projects/sample_project/versions/v1/evals/nonexistent")
    assert response.status_code == 404
