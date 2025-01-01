import os

from mixedvoices import constants, metrics
from mixedvoices.core.project import create_project, load_project
from mixedvoices.evaluation.agents.base_agent import BaseAgent
from mixedvoices.evaluation.eval_prompt_generator import EvalPromptGenerator

os.makedirs(constants.PROJECTS_FOLDER, exist_ok=True)
os.makedirs(constants.TASKS_FOLDER, exist_ok=True)

OPEN_AI_CLIENT = None
