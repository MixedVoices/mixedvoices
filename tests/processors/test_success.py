from unittest.mock import patch

from conftest import needs_openai_key
from mixedvoices.processors.success import get_success


@needs_openai_key
@patch("mixedvoices.models.SUCCESS_MODEL", "gpt-4o-mini")
def test_get_success():
    with open("tests/assets/transcript.txt", "r") as f:
        transcript = f.read()
    with open("tests/assets/success_criteria.txt", "r") as f:
        success_criteria = f.read()
    res = get_success(transcript, success_criteria)
    assert not res["success"]
