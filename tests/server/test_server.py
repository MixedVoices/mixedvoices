from unittest.mock import patch

from fastapi.testclient import TestClient

from mixedvoices.server.server import app

client = TestClient(app)


def test_list_projects_errors(mock_base_folder):
    # Test 500 for unexpected errors
    with patch("mixedvoices.list_projects", side_effect=Exception("Unexpected error")):
        response = client.get("/api/projects")
        assert response.status_code == 500
        assert "Unexpected error" in response.json()["detail"]


def test_create_project_with_metrics(mock_base_folder):
    """Test project creation with metrics"""
    metrics_data = {
        "metrics": [
            {
                "name": "test_metric",
                "definition": "Test definition",
                "scoring": "binary",
                "include_prompt": True,
            }
        ]
    }

    response = client.post(
        "/api/projects",
        params={"name": "empty_project", "success_criteria": "Test criteria"},
        json=metrics_data,
    )
    assert response.status_code == 200
    assert response.json()["project_id"] == "empty_project"

    # Test invalid metrics
    invalid_metrics = {"metrics": []}
    response = client.post(
        "/api/projects", params={"name": "invalid_project"}, json=invalid_metrics
    )
    assert response.status_code == 422


def test_version_operations(empty_project):
    """Test version-related operations"""
    # Update success criteria
    response = client.post(
        "/api/projects/empty_project/success_criteria",
        json={"success_criteria": "Updated criteria"},
    )
    assert response.status_code == 200

    # Test invalid version
    response = client.post(
        "/api/projects/non_existent_project/success_criteria",
        json={"success_criteria": "Updated criteria"},
    )
    assert response.status_code == 404


def test_recording_operations(empty_project, mock_process_recording):
    """Test recording-related operations"""
    # Test recording upload with user channel
    with open("tests/assets/call2.wav", "rb") as f:
        response = client.post(
            "/api/projects/empty_project/versions/v1/recordings",
            files={"file": ("call2.wav", f, "audio/wav")},
            params={"user_channel": "left"},
        )
    assert response.status_code == 200

    # Test invalid user channel
    with open("tests/assets/call2.wav", "rb") as f:
        response = client.post(
            "/api/projects/empty_project/versions/v1/recordings",
            files={"file": ("call2.wav", f, "audio/wav")},
            params={"user_channel": "invalid"},
        )
    assert response.status_code == 400

    # Test invalid project
    with open("tests/assets/call2.wav", "rb") as f:
        response = client.post(
            "/api/projects/nonexistent/versions/v1/recordings",
            files={"file": ("call2.wav", f, "audio/wav")},
            params={"user_channel": "left"},
        )
    assert response.status_code == 404


def test_prompt_generator(mock_base_folder):
    """Test prompt generator endpoint"""
    with patch("mixedvoices.TestCaseGenerator.generate"):
        # Test with agent prompt only
        response = client.post(
            "/api/prompt_generator",
            params={
                "agent_prompt": "Test prompt",
                "user_demographic_info": "Test demographics",
            },
        )
        assert response.status_code == 500
        # Test with transcript
        response = client.post(
            "/api/prompt_generator",
            params={"agent_prompt": "Test prompt", "transcript": "Test transcript"},
        )
        assert response.status_code == 200

        # Test with file
        with open("tests/assets/call2.wav", "rb") as f:
            response = client.post(
                "/api/prompt_generator",
                params={"agent_prompt": "Test prompt"},
                files={"file": ("call2.wav", f, "audio/wav")},
            )
        assert response.status_code == 200

        # Test with description
        response = client.post(
            "/api/prompt_generator",
            params={"agent_prompt": "Test prompt", "description": "Test description"},
        )
        assert response.status_code == 200

        # Test with edge cases
        response = client.post(
            "/api/prompt_generator",
            params={"agent_prompt": "Test prompt", "edge_case_count": 2},
        )
        assert response.status_code == 200

    # Test error handling
    with patch(
        "mixedvoices.TestCaseGenerator.generate", side_effect=Exception("Test error")
    ):
        response = client.post(
            "/api/prompt_generator", params={"agent_prompt": "Test prompt"}
        )
        assert response.status_code == 500


def test_eval_operations(sample_project):
    """Test evaluation-related operations"""
    # Create eval
    eval_data = {
        "test_cases": ["Test case 1", "Test case 2"],
        "metric_names": ["empathy"],
    }
    response = client.post("/api/projects/sample_project/evals", json=eval_data)
    assert response.status_code == 200
    eval_id = response.json()["eval_id"]

    # Get eval details
    response = client.get(f"/api/projects/sample_project/evals/{eval_id}")
    assert response.status_code == 200
    assert response.json()["eval_runs"] == []
    assert response.json()["metrics"] == ["empathy"]
    assert response.json()["test_cases"] == ["Test case 1", "Test case 2"]

    # Test invalid eval ID
    response = client.get("/api/projects/sample_project/evals/invalid")
    assert response.status_code == 404

    # Test invalid project
    response = client.get("/api/projects/nonexistent/evals/123")
    assert response.status_code == 404

    with patch(
        "mixedvoices.core.project.Project.load_evaluator",
        side_effect=Exception("Test error"),
    ):
        response = client.get(f"/api/projects/sample_project/evals/{eval_id}")
        assert response.status_code == 500


def test_recording_flow(sample_project):
    """Test recording flow-related endpoints"""
    # Get version flow
    response = client.get("/api/projects/sample_project/versions/v1/flow")
    assert response.status_code == 200
    assert "steps" in response.json()

    # Get recordings
    response = client.get("/api/projects/sample_project/versions/v1/recordings")
    assert response.status_code == 200
    recordings = response.json()["recordings"]
    assert len(recordings) > 0

    # Get flow for first recording
    recording_id = recordings[0]["id"]
    response = client.get(
        f"/api/projects/sample_project/versions/v1/recordings/{recording_id}/flow"
    )
    assert response.status_code == 200
    assert "steps" in response.json()

    # Get step recordings
    steps = response.json()["steps"]
    for step in steps:
        response = client.get(
            f"/api/projects/sample_project/versions/v1/steps/{step['id']}/recordings"
        )
        assert response.status_code == 200
        assert "recordings" in response.json()


def test_eval_run_operations(sample_project):
    """Test eval run operations"""
    response = client.get("/api/projects/sample_project/evals")
    assert response.status_code == 200
    evals = response.json()["evals"]
    assert len(evals) == 1
    eval_id = evals[0]["eval_id"]
    num_prompts = evals[0]["num_prompts"]

    response = client.get(f"/api/projects/sample_project/evals/{eval_id}")
    assert response.status_code == 200
    assert len(response.json()["eval_runs"]) == 1

    run_id = response.json()["eval_runs"][0]["run_id"]

    response = client.get(f"/api/projects/sample_project/evals/{eval_id}/versions/v1/")
    assert response.status_code == 200
    assert len(response.json()["eval_runs"]) == 1

    new_run_id = response.json()["eval_runs"][0]["run_id"]

    assert run_id == new_run_id

    response = client.get(f"/api/projects/sample_project/evals/{eval_id}/runs/{run_id}")
    assert response.status_code == 200
    assert len(response.json()["results"]) == num_prompts
