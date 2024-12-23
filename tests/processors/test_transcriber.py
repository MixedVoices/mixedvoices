from utils import needs_deepgram_key, needs_openai_key

from mixedvoices.processors.transcriber import (
    transcribe_and_combine_deepgram,
    transcribe_and_combine_openai,
)


def check_transcript(transcript):
    assert "wednesday" in transcript
    assert "appointment" in transcript
    assert "dental" in transcript


@needs_openai_key
def test_openai_transcriber():
    res = transcribe_and_combine_openai(
        "tests/assets/call2_user.wav", "tests/assets/call2_assistant.wav"
    )
    transcript = res[0].lower()
    check_transcript(transcript)


@needs_deepgram_key
def test_deepgram_transcriber():
    res = transcribe_and_combine_deepgram("tests/assets/call2.wav")
    transcript = res[0].lower()
    check_transcript(transcript)
