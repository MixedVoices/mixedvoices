import os

import mixedvoices.constants as constants
from mixedvoices.core.project import Project
from mixedvoices.core.task_manager import TaskManager
from mixedvoices.evaluation.agents.base_agent import BaseAgent
from mixedvoices.utils import validate_name

os.makedirs(constants.ALL_PROJECTS_FOLDER, exist_ok=True)
OPEN_AI_CLIENT = None
TASK_MANAGER = TaskManager()


def create_project(project_name):
    validate_name(project_name, "project_name")
    if project_name in os.listdir(constants.ALL_PROJECTS_FOLDER):
        raise ValueError(f"Project {project_name} already exists")
    os.makedirs(os.path.join(constants.ALL_PROJECTS_FOLDER, project_name))
    return Project(project_name)


def load_project(project_name):
    if project_name not in os.listdir(constants.ALL_PROJECTS_FOLDER):
        raise ValueError(f"Project {project_name} does not exist")
    return Project(project_name)
