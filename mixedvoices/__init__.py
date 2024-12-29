import os
from typing import List

import mixedvoices.constants as constants
import mixedvoices.metrics as metrics
from mixedvoices.core.project import Project
from mixedvoices.core.task_manager import TaskManager
from mixedvoices.evaluation.agents.base_agent import BaseAgent
from mixedvoices.evaluation.eval_generator import EvalGenerator
from mixedvoices.utils import validate_name

os.makedirs(constants.PROJECTS_FOLDER, exist_ok=True)
os.makedirs(constants.TASKS_FOLDER, exist_ok=True)

OPEN_AI_CLIENT = None
TASK_MANAGER = TaskManager()


def create_project(project_name: str, metrics: List[metrics.Metric]):
    """Create a new project"""
    validate_name(project_name, "project_name")
    if project_name in os.listdir(constants.PROJECTS_FOLDER):
        raise ValueError(f"Project {project_name} already exists")
    os.makedirs(os.path.join(constants.PROJECTS_FOLDER, project_name))
    return Project(project_name, metrics)


def load_project(project_name: str):
    """Load an existing project"""
    if project_name not in os.listdir(constants.PROJECTS_FOLDER):
        raise ValueError(f"Project {project_name} does not exist")
    return Project(project_name)
