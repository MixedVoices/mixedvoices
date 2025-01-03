from unittest.mock import patch

import pytest

from conftest import needs_deepgram_key, needs_openai_key
from mixedvoices.core.utils import get_transcript_and_duration


def check_transcript(transcript):
    assert "wednesday" in transcript
    assert "appointment" in transcript
    assert "dental" in transcript


@needs_openai_key
@patch("mixedvoices.models.TRANSCRIPTION_MODEL", "openai/whisper-1")
def test_openai_transcriber(tmp_path):
    with pytest.raises(ValueError):
        get_transcript_and_duration("tests/assets/call2.wav", tmp_path, "top")

    with pytest.raises(ValueError):
        get_transcript_and_duration("tests/assets/call2_user.wav", tmp_path)
    transcript, _, _, duration = get_transcript_and_duration(
        "tests/assets/call2.wav", tmp_path
    )
    check_transcript(transcript.lower())

    assert round(duration) == 76


@needs_deepgram_key
@patch("mixedvoices.models.TRANSCRIPTION_MODEL", "deepgram/nova-2")
def test_deepgram_transcriber(tmp_path):
    transcript, _, _, duration = get_transcript_and_duration(
        "tests/assets/call2.wav", tmp_path
    )
    check_transcript(transcript.lower())

    assert round(duration) == 76
