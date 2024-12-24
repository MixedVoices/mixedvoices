from unittest.mock import patch

from conftest import needs_openai_key
from mixedvoices.processors.summary import summarize_transcript


@needs_openai_key
@patch("mixedvoices.models.SUMMARY_MODEL", "gpt-4o-mini")
def test_get_summary():
    with open("tests/assets/transcript.txt", "r") as f:
        transcript = f.read()
    summary = summarize_transcript(transcript)
    assert len(summary.split(".")) < 5
