import os
from typing import List

import mixedvoices.constants as constants
from mixedvoices.core.project import Project
from mixedvoices.core.task_manager import TaskManager
from mixedvoices.evaluation.agents.base_agent import BaseAgent
from mixedvoices.evaluation.eval_generator import EvalGenerator
from mixedvoices.metrics.api import (
    add_metric,
    get_metric,
    get_metrics,
    list_metric_names,
    list_metrics,
    remove_metric,
    reset_metrics,
    update_metric,
)
from mixedvoices.utils import validate_name

os.makedirs(constants.PROJECTS_FOLDER, exist_ok=True)
os.makedirs(constants.TASKS_FOLDER, exist_ok=True)

OPEN_AI_CLIENT = None
TASK_MANAGER = TaskManager()


def create_project(project_name: str, metric_names: List[str]):
    """Create a new project"""
    validate_name(project_name, "project_name")
    get_metrics(metric_names)  # checks existence
    if project_name in os.listdir(constants.PROJECTS_FOLDER):
        raise ValueError(f"Project {project_name} already exists")
    os.makedirs(os.path.join(constants.PROJECTS_FOLDER, project_name))
    return Project(project_name, metric_names)


def load_project(project_name: str):
    """Load an existing project"""
    if project_name not in os.listdir(constants.PROJECTS_FOLDER):
        raise ValueError(f"Project {project_name} does not exist")
    return Project(project_name)
