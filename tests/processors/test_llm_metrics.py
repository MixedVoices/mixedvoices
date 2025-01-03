from unittest.mock import patch

from conftest import needs_openai_key
from mixedvoices.metrics import get_all_default_metrics
from mixedvoices.processors.llm_metrics import generate_scores


@needs_openai_key
@patch("mixedvoices.models.METRICS_MODEL", "gpt-4o-mini")
def test_generate_scores():
    with open("tests/assets/transcript.txt", "r") as f:
        transcript = f.read()
    with open("tests/assets/prompt.txt", "r") as f:
        prompt = f.read()

    default_metrics = get_all_default_metrics()
    scores = generate_scores(transcript, prompt, default_metrics)
    for metric in default_metrics:
        assert metric.name in scores
        score = scores[metric.name]
        assert score["score"] in metric.expected_values
