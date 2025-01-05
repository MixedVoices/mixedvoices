import os
import sys

from mixedvoices import constants, metrics, models
from mixedvoices.core.project import create_project, load_project
from mixedvoices.evaluation.agents.base_agent import BaseAgent
from mixedvoices.evaluation.test_case_generator import TestCaseGenerator

os.makedirs(constants.PROJECTS_FOLDER, exist_ok=True)
os.makedirs(constants.TASKS_FOLDER, exist_ok=True)


def check_keys():
    exempt_commands = ["config"]
    if len(sys.argv) > 1 and any(cmd in sys.argv[1:] for cmd in exempt_commands):
        return
    required_keys = ["OPENAI_API_KEY"]
    if models.TRANSCRIPTION_MODEL == "deepgram/nova-2":
        required_keys.append("DEEPGRAM_API_KEY")

    missing_keys = [key for key in required_keys if key not in os.environ]
    if missing_keys:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing_keys)}. \nThese keys reflect models being used currently. You can change the models by running 'mixedvoices config'."
        )


def list_projects():
    if not os.path.exists(constants.PROJECTS_FOLDER):
        return []
    return os.listdir(constants.PROJECTS_FOLDER)


check_keys()
OPEN_AI_CLIENT = None
