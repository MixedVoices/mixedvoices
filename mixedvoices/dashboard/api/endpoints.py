# Projet endpoints
def projects_ep() -> str:
    return "projects"


def project_success_criteria_ep(project_name: str) -> str:
    return f"projects/{project_name}/success_criteria"


def project_metrics_ep(project_name: str) -> str:
    return f"projects/{project_name}/metrics"


def default_metrics_ep() -> str:
    return "default_metrics"


def list_versions_ep(project_name: str) -> str:
    return f"projects/{project_name}/versions"


def version_ep(project_name: str, version_name: str) -> str:
    return f"/api/projects/{project_name}/versions/{version_name}"


def version_flow_ep(project_name: str, version_name: str) -> str:
    return f"projects/{project_name}/versions/{version_name}/flow"


def version_recordings_ep(project_name: str, version_name: str) -> str:
    return f"projects/{project_name}/versions/{version_name}/recordings"


def step_recordings_ep(project_name: str, version_name: str, step_id: str) -> str:
    return f"projects/{project_name}/versions/{version_name}/steps/{step_id}/recordings"


def recording_flow_ep(project_name: str, version_name: str, recording_id: str) -> str:
    return f"projects/{project_name}/versions/{version_name}/recordings/{recording_id}/flow"


def list_evals_ep(project_name: str) -> str:
    """Get endpoint for listing evaluations"""
    return f"projects/{project_name}/evals"


def eval_details_ep(project_name: str, eval_id: str) -> str:
    """Get endpoint for getting evaluation details"""
    return f"projects/{project_name}/evals/{eval_id}"


def version_eval_details_ep(project_name: str, version_name: str, eval_id: str) -> str:
    return f"/api/projects/{project_name}/evals/{eval_id}/versions/{version_name}"


def eval_run_details_ep(project_name: str, eval_id: str, run_id: str) -> str:
    """Get endpoint for getting evaluation run details"""
    return f"projects/{project_name}/evals/{eval_id}/runs/{run_id}"
