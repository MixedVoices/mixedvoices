def projects_ep() -> str:
    return "projects"


def project_success_criteria_ep(project_id: str) -> str:
    return f"projects/{project_id}/success_criteria"


def project_metrics_ep(project_id: str) -> str:
    return f"projects/{project_id}/metrics"


def default_metrics_ep() -> str:
    return "default_metrics"


def metric_ep(project_id: str, metric_name: str) -> str:
    return f"projects/{project_id}/metrics/{metric_name}"


def project_versions_ep(project_id: str) -> str:
    return f"projects/{project_id}/versions"


def version_ep(project_id: str, version_id: str) -> str:
    return f"projects/{project_id}/versions/{version_id}"


def version_flow_ep(project_id: str, version_id: str) -> str:
    return f"projects/{project_id}/versions/{version_id}/flow"


def version_recordings_ep(project_id: str, version_id: str) -> str:
    return f"projects/{project_id}/versions/{version_id}/recordings"


def step_recordings_ep(project_id: str, version_id: str, step_id: str) -> str:
    return f"projects/{project_id}/versions/{version_id}/steps/{step_id}/recordings"


def recording_flow_ep(project_id: str, version_id: str, recording_id: str) -> str:
    return f"projects/{project_id}/versions/{version_id}/recordings/{recording_id}/flow"


def evals_ep(project_id: str) -> str:
    return f"projects/{project_id}/evals"


def eval_details_ep(project_id: str, eval_id: str) -> str:
    """Get endpoint for getting evaluation details"""
    return f"projects/{project_id}/evals/{eval_id}"


def version_eval_details_ep(project_id: str, version_id: str, eval_id: str) -> str:
    return f"projects/{project_id}/evals/{eval_id}/versions/{version_id}"


def eval_run_details_ep(project_id: str, eval_id: str, run_id: str) -> str:
    """Get endpoint for getting evaluation run details"""
    return f"projects/{project_id}/evals/{eval_id}/runs/{run_id}"


def prompt_generator_ep() -> str:
    return "prompt_generator"
