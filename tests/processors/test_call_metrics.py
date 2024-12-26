import json

from openai.types.audio import TranscriptionWord
from pytest import approx

from mixedvoices.processors.call_metrics import (
    calculate_latency_and_interruptions,
    calculate_stereo_snr,
    calculate_wpm,
)


def test_clean_audio():
    clean_audio_path = "tests/assets/call2.wav"
    left_snr, right_snr = calculate_stereo_snr(clean_audio_path)
    assert left_snr == right_snr == "N/A"


def test_noisy_audio():
    noisy_audio_path = "tests/assets/call2_noisy.wav"
    left_snr, right_snr = calculate_stereo_snr(noisy_audio_path)
    assert float(left_snr.split()[0]) > 0
    assert float(right_snr.split()[0]) > 0


def load_words(file_path):
    with open(file_path, "r") as f:
        words = json.load(f)

    return [
        TranscriptionWord(word=word["word"], start=word["start"], end=word["end"])
        for word in words
    ]


def test_latency_and_interruptions():
    user_words = load_words("tests/assets/user_words.json")
    agent_words = load_words("tests/assets/agent_words.json")

    res = calculate_latency_and_interruptions(user_words, agent_words, 76)
    assert res["average_latency"] == approx(1.587)
    assert res["user_interruptions_per_minute"] == 0
    assert res["agent_interruptions_per_minute"] == 0


def test_wpm():
    agent_words = load_words("tests/assets/agent_words.json")
    agent_wpm = calculate_wpm(agent_words)
    assert agent_wpm == approx(184.307, rel=1e-3)

    user_words = load_words("tests/assets/user_words.json")
    user_wpm = calculate_wpm(user_words)

    assert user_wpm == approx(167.579, rel=1e-3)
