import os

from mixedvoices.constants import ALL_PROJECTS_FOLDER
from mixedvoices.core.project import Project

os.makedirs(ALL_PROJECTS_FOLDER, exist_ok=True)


def create_project(name):
    if name in os.listdir(ALL_PROJECTS_FOLDER):
        raise ValueError(f"Project {name} already exists")
    os.makedirs(os.path.join(ALL_PROJECTS_FOLDER, name))
    return Project(name)


def load_project(name):
    if name not in os.listdir(ALL_PROJECTS_FOLDER):
        raise ValueError(f"Project {name} does not exist")
    return Project(name)
