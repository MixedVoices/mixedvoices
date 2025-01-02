import os

from mixedvoices import constants, metrics, models
from mixedvoices.core.project import create_project, load_project
from mixedvoices.evaluation.agents.base_agent import BaseAgent
from mixedvoices.evaluation.eval_prompt_generator import EvalPromptGenerator

os.makedirs(constants.PROJECTS_FOLDER, exist_ok=True)
os.makedirs(constants.TASKS_FOLDER, exist_ok=True)


def check_keys():
    required_keys = ["OPENAI_API_KEY"]
    if models.TRANSCRIPTION_MODEL == "deepgram/nova-2":
        required_keys.append("DEEPGRAM_API_KEY")

    for key in required_keys:
        if key not in os.environ:
            raise ValueError(f"Environment variable {key} not set")


check_keys()
OPEN_AI_CLIENT = None
