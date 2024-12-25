from unittest.mock import patch

from conftest import needs_openai_key
from mixedvoices.processors.steps import script_to_step_names


@needs_openai_key
@patch("mixedvoices.models.STEPS_MODEL", "gpt-4o-mini")
def test_steps():
    with open("tests/assets/transcript.txt", "r") as f:
        transcript = f.read()

    existing_step_names = ["Greeting"]

    steps = script_to_step_names(transcript, existing_step_names)
    for step in steps:
        assert len(step.split()) < 7
