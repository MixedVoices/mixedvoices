from typing import Tuple
from unittest.mock import patch

import mixedvoices as mv
from conftest import needs_deepgram_key, needs_openai_key
from examples.evaluation.agent import DentalAgent, check_conversation_ended
from mixedvoices.evaluation.agents.base_agent import BaseAgent


class MyDentalAgent(BaseAgent):
    def __init__(self, model):
        self.agent = DentalAgent(model=model)

    def respond(self, input_text: str) -> Tuple[str, bool]:
        response = self.agent.get_response(input_text)
        has_conversation_ended = check_conversation_ended(response)
        return response, has_conversation_ended


@needs_openai_key
@needs_deepgram_key
@patch("mixedvoices.constants.TRANSCRIPTION_PROVIDER", "deepgram")
def test_full(temp_project_folder):
    project = mv.create_project("test_project")
    with open("tests/assets/prompt.txt", "r") as f:
        prompt = f.read()
    success_criteria = (
        "The call is successful if an appointment is scheduled and confirmed."
    )
    version = project.create_version(
        "v1", prompt=prompt, success_criteria=success_criteria
    )
    version.add_recording("tests/assets/call1.wav")
    version.add_recording("tests/assets/call2.wav")

    for recording in version.recordings.values():
        if recording.audio_path.endswith("call1.wav"):
            assert recording.is_successful
        else:
            assert not recording.is_successful

    evaluator = version.create_evaluator(1, 1, 1)
    evaluator.run(MyDentalAgent, agent_starts=None, model="gpt-4o-mini")

    project = mv.load_project("test_project")
    version = project.load_version("v1")

    assert len(version.evals) == 1

    # get the first eval from dict
    cur_eval = list(version.evals.values())[0]
    eval_agents = cur_eval.eval_agents
    assert len(eval_agents) == 3

    for eval_agent in eval_agents:
        assert eval_agent.prompt == prompt
        assert eval_agent.ended
        assert eval_agent.transcript
        assert eval_agent.scores
