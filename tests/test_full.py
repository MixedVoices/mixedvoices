from typing import Tuple
from unittest.mock import patch

import pytest

import mixedvoices as mv
from conftest import needs_deepgram_key, needs_openai_key
from examples.evaluation.agent import DentalAgent, check_conversation_ended
from mixedvoices.evaluation.agents.base_agent import BaseAgent
from mixedvoices.metrics import Metric, empathy


class MyDentalAgent(BaseAgent):
    def __init__(self, model):
        self.agent = DentalAgent(model=model)

    def respond(self, input_text: str) -> Tuple[str, bool]:
        response = self.agent.get_response(input_text)
        has_conversation_ended = check_conversation_ended(response)
        return response, has_conversation_ended


@needs_openai_key
@needs_deepgram_key
@patch("mixedvoices.models.TRANSCRIPTION_MODEL", "deepgram/nova-2")
def test_full(mock_base_folder):
    assert mv.list_projects() == []
    friendliness = Metric(
        name="friendliness",
        definition="How friendly the agent is from a scale of 0-10",
        scoring="continuous",
    )

    with pytest.raises(ValueError):
        friendliness = Metric(
            name="friendliness",
            definition="How friendly the agent is from a scale of 0-10",
            scoring="invalid",
        )
    success_criteria = (
        "The call is successful if an appointment is scheduled and confirmed."
    )
    project = mv.create_project(
        "empty_project",
        metrics=[empathy, friendliness],
        success_criteria=success_criteria,
    )
    assert mv.list_projects() == ["empty_project"]

    assert project.get_metric("friendliness").scoring == "continuous"
    with pytest.raises(KeyError):
        project.get_metric("unknown_metric")
    with open("tests/assets/prompt.txt", "r") as f:
        prompt = f.read()
    version = project.create_version("v1", prompt=prompt)
    version.add_recording("tests/assets/call1.wav")
    version.add_recording("tests/assets/call2.wav")

    for recording in version._recordings.values():
        if recording.audio_path.endswith("call1.wav"):
            assert recording.is_successful
        else:
            assert not recording.is_successful

    with open("tests/assets/transcript.txt", "r") as f:
        transcript = f.read()

    test_generator = mv.TestCaseGenerator(prompt)
    test_generator.add_from_transcripts([transcript]).add_edge_cases(
        1
    ).add_from_descriptions(["A young man from New York"]).add_from_project(
        project
    ).add_from_version(
        version
    ).add_from_recordings(
        ["tests/assets/call2.wav"]
    )
    assert test_generator.num_cases == 8
    test_cases = test_generator.generate()

    evaluator = project.create_evaluator(test_cases, metric_names=None)
    eval_id = evaluator.id
    run = evaluator.run(version, MyDentalAgent, agent_starts=None, model="gpt-4o-mini")

    assert len(evaluator.list_eval_runs()) == 1
    loaded_evaluator = project.load_evaluator(eval_id)
    assert loaded_evaluator.id == evaluator.id
    assert len(loaded_evaluator.list_eval_runs()) == 1
    loaded_run = loaded_evaluator.load_eval_run(run.id)

    for r in [run, loaded_run]:
        assert len(r.results) == 8
        assert r.status == "COMPLETED"
        assert r.eval_id == eval_id
        assert r.project_id == project.id
        assert r.version_id == version.id
        for result in r.results:
            assert result["error"] is None
            assert result["success_explanation"] is not None
            assert result["is_successful"] is not None
            assert result["transcript"] is not None
            assert result["started"]
            assert result["ended"]
            assert "empathy" in result["scores"]
            assert "friendliness" in result["scores"]

        with pytest.raises(ValueError):
            r.run(MyDentalAgent, agent_starts=False, model="gpt-4o-mini")
