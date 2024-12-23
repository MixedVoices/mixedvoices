def get_projects_endpoint() -> str:
    return "projects"


def get_project_versions_endpoint(project_id: str) -> str:
    return f"projects/{project_id}/versions"


def get_version_flow_endpoint(project_id: str, version: str) -> str:
    return f"projects/{project_id}/versions/{version}/flow"


def get_version_recordings_endpoint(project_id: str, version: str) -> str:
    return f"projects/{project_id}/versions/{version}/recordings"


def get_step_recordings_endpoint(project_id: str, version: str, step_id: str) -> str:
    return f"projects/{project_id}/versions/{version}/steps/{step_id}/recordings"


def get_recording_flow_endpoint(
    project_id: str, version: str, recording_id: str
) -> str:
    return f"projects/{project_id}/versions/{version}/recordings/{recording_id}/flow"


def list_evals_endpoint(project_name: str, version_name: str) -> str:
    """Get endpoint for listing evaluations"""
    return f"projects/{project_name}/versions/{version_name}/evals"


def get_eval_details_endpoint(project_name: str, version_name: str, eval_id: str) -> str:
    """Get endpoint for getting evaluation details"""
    return f"projects/{project_name}/versions/{version_name}/evals/{eval_id}"
