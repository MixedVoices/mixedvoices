import os

import mixedvoices.constants as constants
from mixedvoices.core.project import Project
from mixedvoices.core.task_manager import TaskManager

task_manager = TaskManager()
os.makedirs(constants.ALL_PROJECTS_FOLDER, exist_ok=True)
OPEN_AI_CLIENT = None


def create_project(name):
    if name in os.listdir(constants.ALL_PROJECTS_FOLDER):
        raise ValueError(f"Project {name} already exists")
    os.makedirs(os.path.join(constants.ALL_PROJECTS_FOLDER, name))
    return Project(name)


def load_project(name):
    if name not in os.listdir(constants.ALL_PROJECTS_FOLDER):
        raise ValueError(f"Project {name} does not exist")
    return Project(name)
