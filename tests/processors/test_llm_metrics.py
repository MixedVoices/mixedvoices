from unittest.mock import patch

from utils import needs_openai_key

from mixedvoices.processors.llm_metrics import get_llm_metrics


@needs_openai_key
@patch("mixedvoices.models.METRICS_MODEL", "gpt-4o-mini")
def test_get_llm_metrics():
    with open("tests/assets/transcript.txt", "r") as f:
        transcript = f.read()
    with open("tests/assets/prompt.txt", "r") as f:
        prompt = f.read()
    metrics = get_llm_metrics(transcript, prompt)

    metric_scoring = {
        "empathy": list(range(11)),
        "repetition": ["PASS", "FAIL", "N/A"],
        "conciseness": list(range(11)),
        "hallucination": ["PASS", "FAIL"],
        "context": ["PASS", "FAIL"],
        "scheduling": list(range(11)) + ["N/A"],
        "adaptive_qa": list(range(11)) + ["N/A"],
        "objection_handling": list(range(11)),
    }

    for metric, scores in metric_scoring.items():
        assert metrics[metric]["score"] in scores
