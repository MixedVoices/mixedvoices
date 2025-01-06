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

    # Test invalid project name
    response = client.post(
        "/api/projects",
        params={"name": "has space", "success_criteria": None},
        json=metrics_data,
    )
    assert response.status_code == 400

    # Test project already exists
    response = client.post(
        "/api/projects",
        params={"name": "empty_project", "success_criteria": None},
        json=metrics_data,
    )
    assert response.status_code == 409

    # Mock error
    with patch(
        "mixedvoices.create_project",
        side_effect=Exception("Test error"),
    ):
        response = client.post(
            "/api/projects",
            params={"name": "new_project", "success_criteria": None},
            json=metrics_data,
        )
        assert response.status_code == 500

    # update metric
    response = client.post(
        "/api/projects/empty_project/metrics/test_metric",
        json={
            "name": "test_metric",
            "definition": "Updated definition",
            "scoring": "continuous",
            "include_prompt": False,
        },
    )
    assert response.status_code == 200
    # list metrics
    response = client.get("/api/projects/empty_project/metrics")
    assert response.status_code == 200
    assert response.json()["metrics"][0]["name"] == "test_metric"
    assert response.json()["metrics"][0]["definition"] == "Updated definition"
    assert response.json()["metrics"][0]["scoring"] == "continuous"
    assert not response.json()["metrics"][0]["include_prompt"]

    # list non-existent project metrics
    response = client.get("/api/projects/nonexistent/metrics")
    assert response.status_code == 404

    # mock error while listing metrics
    with patch(
        "mixedvoices.load_project",
        side_effect=Exception("Test error"),
    ):
        response = client.get("/api/projects/empty_project/metrics")
        assert response.status_code == 500

    # update non-existent metric
    response = client.post(
        "/api/projects/empty_project/metrics/nonexistent_metric",
        json={
            "name": "nonexistent_metric",
            "definition": "Updated definition",
            "scoring": "continuous",
            "include_prompt": False,
        },
    )
    assert response.status_code == 404

    # mock error
    with patch(
        "mixedvoices.core.project.Project.update_metric",
        side_effect=Exception("Test error"),
    ):
        response = client.post(
            "/api/projects/empty_project/metrics/test_metric",
            json={
                "name": "test_metric",
                "definition": "Updated definition",
                "scoring": "continuous",
                "include_prompt": False,
            },
        )
        assert response.status_code == 500

    # add metric
    response = client.post(
        "/api/projects/empty_project/metrics",
        json={
            "name": "test_metric2",
            "definition": "Test definition",
            "scoring": "binary",
            "include_prompt": True,
        },
    )
    assert response.status_code == 200

    # Metric already exists
    response = client.post(
        "/api/projects/empty_project/metrics",
        json={
            "name": "test_metric",
            "definition": "Test definition",
            "scoring": "binary",
            "include_prompt": True,
        },
    )
    assert response.status_code == 409

    # Project not found
    response = client.post(
        "/api/projects/nonexistent/metrics",
        json={
            "name": "test_metric2",
            "definition": "Test definition",
            "scoring": "binary",
            "include_prompt": True,
        },
    )
    assert response.status_code == 404

    # Mock error
    with patch(
        "mixedvoices.core.project.Project.add_metrics",
        side_effect=Exception("Test error"),
    ):
        response = client.post(
            "/api/projects/empty_project/metrics",
            json={
                "name": "test_metric2",
                "definition": "Test definition",
                "scoring": "binary",
                "include_prompt": True,
            },
        )
        assert response.status_code == 500


def test_list_default_metrics(empty_project):
    response = client.get("/api/default_metrics")
    assert response.status_code == 200
    assert "metrics" in response.json()

    # mock error
    with patch(
        "mixedvoices.metrics.get_all_default_metrics",
        side_effect=Exception("Test error"),
    ):
        response = client.get("/api/default_metrics")
        assert response.status_code == 500


def test_version_operations(empty_project):
    """Test version-related operations"""
    # create a version
    response = client.post(
        "/api/projects/empty_project/versions",
        json={"name": "v2", "prompt": "Test prompt"},
    )
    assert response.status_code == 200

    # Test invalid project
    response = client.post(
        "/api/projects/nonexistent/versions",
        json={"name": "v3", "prompt": "Test prompt"},
    )
    assert response.status_code == 404

    # test version exists
    response = client.post(
        "/api/projects/empty_project/versions",
        json={"name": "v1", "prompt": "Test prompt"},
    )
    assert response.status_code == 409

    # invalid version name
    response = client.post(
        "/api/projects/empty_project/versions",
        json={"name": "has space", "prompt": "Test prompt"},
    )
    assert response.status_code == 400

    # Mock error
    with patch(
        "mixedvoices.core.project.Project.create_version",
        side_effect=Exception("Test error"),
    ):
        response = client.post(
            "/api/projects/empty_project/versions",
            json={"name": "v2", "prompt": "Test prompt"},
        )
        assert response.status_code == 500

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

    # Mock error
    with patch(
        "mixedvoices.core.project.Project.update_success_criteria",
        side_effect=Exception("Test error"),
    ):
        response = client.post(
            "/api/projects/empty_project/success_criteria",
            json={"success_criteria": "Updated criteria"},
        )
        assert response.status_code == 500

    # get success criteria
    response = client.get("/api/projects/empty_project/success_criteria")
    assert response.status_code == 200

    # Test invalid project
    response = client.get("/api/projects/non_existent_project/success_criteria")
    assert response.status_code == 404

    # Mock error
    with patch(
        "mixedvoices.load_project",
        side_effect=Exception("Test error"),
    ):
        response = client.get("/api/projects/empty_project/success_criteria")
        assert response.status_code == 500

    # list versions
    response = client.get("/api/projects/empty_project/versions")
    assert response.status_code == 200
    assert response.json()["versions"][0]["name"] == "v1"
    assert response.json()["versions"][1]["name"] == "v2"

    # Test invalid project
    response = client.get("/api/projects/non_existent_project/versions")
    assert response.status_code == 404

    # Mock error while listing versions
    with patch(
        "mixedvoices.core.project.Project.load_version",
        side_effect=Exception("Test error"),
    ):
        response = client.get("/api/projects/empty_project/versions")
        assert response.status_code == 500

    # Get version details
    response = client.get("/api/projects/empty_project/versions/v1")
    assert response.status_code == 200
    assert response.json()["name"] == "v1"

    # Test invalid version
    response = client.get("/api/projects/empty_project/versions/invalid")
    assert response.status_code == 404

    # Mock error while getting version details
    with patch(
        "mixedvoices.core.project.Project.load_version",
        side_effect=Exception("Test error"),
    ):
        response = client.get("/api/projects/empty_project/versions/v1")
        assert response.status_code == 500


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

    # mock error
    with patch(
        "mixedvoices.core.version.Version.add_recording",
        side_effect=Exception("Test error"),
    ):
        with open("tests/assets/call2.wav", "rb") as f:
            response = client.post(
                "/api/projects/empty_project/versions/v1/recordings",
                files={"file": ("call2.wav", f, "audio/wav")},
                params={"user_channel": "left"},
            )
        assert response.status_code == 500


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

    # test invalid project
    response = client.post("/api/projects/nonexistent/evals", json=eval_data)
    assert response.status_code == 404

    # mock error
    with patch(
        "mixedvoices.core.project.Project.create_evaluator",
        side_effect=Exception("Test error"),
    ):
        response = client.post("/api/projects/sample_project/evals", json=eval_data)
        assert response.status_code == 500

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

    # version flow project doesn't exist
    response = client.get("/api/projects/nonexistent/versions/v1/flow")
    assert response.status_code == 404

    # Mock error
    with patch(
        "mixedvoices.core.project.Project.load_version",
        side_effect=Exception("Test error"),
    ):
        response = client.get("/api/projects/sample_project/versions/v1/flow")
        assert response.status_code == 500

    # Get recordings
    response = client.get("/api/projects/sample_project/versions/v1/recordings")
    assert response.status_code == 200
    recordings = response.json()["recordings"]
    assert len(recordings) > 0

    # Test invalid project
    response = client.get("/api/projects/nonexistent/versions/v1/recordings")
    assert response.status_code == 404

    # Mock error
    with patch(
        "mixedvoices.core.project.Project.load_version",
        side_effect=Exception("Test error"),
    ):
        response = client.get("/api/projects/sample_project/versions/v1/recordings")
        assert response.status_code == 500

    # Get flow for first recording
    recording_id = recordings[0]["id"]
    response = client.get(
        f"/api/projects/sample_project/versions/v1/recordings/{recording_id}/flow"
    )
    assert response.status_code == 200
    assert "steps" in response.json()
    steps = response.json()["steps"]

    # Test invalid recording ID
    response = client.get(
        "/api/projects/sample_project/versions/v1/recordings/invalid/flow"
    )
    assert response.status_code == 404

    # mock error
    with patch(
        "mixedvoices.core.project.Project.load_version",
        side_effect=Exception("Test error"),
    ):
        response = client.get(
            f"/api/projects/sample_project/versions/v1/recordings/{recording_id}/flow"
        )
        assert response.status_code == 500

    # Get step recordings
    for step in steps:
        response = client.get(
            f"/api/projects/sample_project/versions/v1/steps/{step['id']}/recordings"
        )
        assert response.status_code == 200
        assert "recordings" in response.json()

    # Test invalid step ID
    response = client.get(
        "/api/projects/sample_project/versions/v1/steps/invalid/recordings"
    )
    assert response.status_code == 404

    # Mock error
    with patch(
        "mixedvoices.core.version.Version.get_step",
        side_effect=Exception("Test error"),
    ):
        response = client.get(
            f"/api/projects/sample_project/versions/v1/steps/{step['id']}/recordings"
        )
        assert response.status_code == 500


def test_eval_run_operations(sample_project):
    """Test eval run operations"""
    response = client.get("/api/projects/sample_project/evals")
    assert response.status_code == 200
    evals = response.json()["evals"]
    assert len(evals) == 1
    eval_id = evals[0]["eval_id"]
    num_prompts = evals[0]["num_prompts"]

    # Test invalid project
    response = client.get("/api/projects/nonexistent/evals/")
    assert response.status_code == 404

    # Test mock error
    with patch(
        "mixedvoices.core.project.Project.list_evaluators",
        side_effect=Exception("Test error"),
    ):
        response = client.get("/api/projects/sample_project/evals")
        assert response.status_code == 500

    response = client.get(f"/api/projects/sample_project/evals/{eval_id}")
    assert response.status_code == 200
    assert len(response.json()["eval_runs"]) == 1

    run_id = response.json()["eval_runs"][0]["run_id"]

    # Test invalid project
    response = client.get(f"/api/projects/invalid/evals/{eval_id}")
    assert response.status_code == 404

    # Test mock error
    with patch(
        "mixedvoices.core.project.Project.load_evaluator",
        side_effect=Exception("Test error"),
    ):
        response = client.get(f"/api/projects/sample_project/evals/{eval_id}")
        assert response.status_code == 500

    response = client.get(f"/api/projects/sample_project/evals/{eval_id}/versions/v1/")
    assert response.status_code == 200
    assert len(response.json()["eval_runs"]) == 1

    new_run_id = response.json()["eval_runs"][0]["run_id"]

    assert run_id == new_run_id

    # Test invalid project
    response = client.get(f"/api/projects/invalid/evals/{eval_id}/versions/v1/")
    assert response.status_code == 404

    # Test mock error
    with patch(
        "mixedvoices.core.project.Project.load_evaluator",
        side_effect=Exception("Test error"),
    ):
        response = client.get(
            f"/api/projects/sample_project/evals/{eval_id}/versions/v1/"
        )
        assert response.status_code == 500

    response = client.get(f"/api/projects/sample_project/evals/{eval_id}/runs/{run_id}")
    assert response.status_code == 200
    assert len(response.json()["results"]) == num_prompts

    # Test invalid project
    response = client.get(f"/api/projects/invalid/evals/{eval_id}/runs/{run_id}")
    assert response.status_code == 404

    # Test mock error
    with patch(
        "mixedvoices.core.project.Project.load_evaluator",
        side_effect=Exception("Test error"),
    ):
        response = client.get(
            f"/api/projects/sample_project/evals/{eval_id}/runs/{run_id}"
        )
        assert response.status_code == 500
