import atexit
import os
from concurrent.futures import ThreadPoolExecutor
from typing import List

import requests
from httpx import RequestError
from openai.types.audio import TranscriptionVerbose, TranscriptionWord

from mixedvoices.utils import get_openai_client

TRANSCRIPTION_POOL = ThreadPoolExecutor(max_workers=2, thread_name_prefix="Transcriber")
atexit.register(lambda: TRANSCRIPTION_POOL.shutdown(wait=True))


def transcribe_with_openai(audio_path):
    client = get_openai_client()
    with open(audio_path, "rb") as audio_file:
        json_response: TranscriptionVerbose = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="verbose_json",
            timestamp_granularities=["word"],
        )

    assert json_response.words is not None
    return json_response.text, json_response.words


def make_deepgram_request(audio_path):
    api_key = os.getenv("DEEPGRAM_API_KEY")
    if not api_key:
        raise ValueError("DEEPGRAM_API_KEY environment variable not set")
    url = "https://api.deepgram.com/v1/listen"
    params = {
        "utterances": "true",
        "multichannel": "true",
        "punctuate": "true",
        "model": "nova-2",
        "numerals": "true",
    }
    headers = {"Authorization": f"Token {api_key}", "Content-Type": "audio/wav"}

    with open(audio_path, "rb") as audio_file:
        try:
            response = requests.post(
                url, params=params, headers=headers, data=audio_file
            )
            response.raise_for_status()  # Raise exception for error status codes
            return response.json()
        except requests.exceptions.RequestException as e:
            raise RequestError(f"API request failed: {str(e)}") from e


def format_deepgram_words(words):
    return [
        TranscriptionWord(
            word=word["punctuated_word"], start=word["start"], end=word["end"]
        )
        for word in words
    ]


def transcribe_with_deepgram(audio_path, user_channel="left"):
    """
    Transcribe audio using Deepgram API

    Args:
        audio_file_path (str): Path to the audio file to transcribe
        user_channel (str): Channel containing user audio ("left" or "right")
    """
    response = make_deepgram_request(audio_path)

    user_idx = 0 if user_channel == "left" else 1
    agent_idx = 1 - user_idx

    user_response = response["results"]["channels"][user_idx]["alternatives"][0]
    agent_response = response["results"]["channels"][agent_idx]["alternatives"][
        0
    ]
    user_words = format_deepgram_words(user_response["words"])
    user_transcript = user_response["transcript"]
    agent_words = format_deepgram_words(agent_response["words"])
    agent_transcript = agent_response["transcript"]

    return user_transcript, user_words, agent_transcript, agent_words


def create_combined_transcript(
    user_words: List[TranscriptionWord], agent_words: List[TranscriptionWord]
):
    last_speaker = None
    user_index, agent_index = 0, 0
    all_segments = []
    current_segment = []
    while user_index < len(user_words) or agent_index < len(agent_words):
        user_word = user_words[user_index] if user_index < len(user_words) else None
        agent_word = (
            agent_words[agent_index]
            if agent_index < len(agent_words)
            else None
        )

        if not agent_word or (user_word and user_word.start < agent_word.start):
            speaker = "user"
            current_word = user_word
            user_index += 1
        else:
            speaker = "bot"
            current_word = agent_word
            agent_index += 1

        if last_speaker != speaker:
            if current_segment:
                all_segments.append(current_segment)
            current_segment = [f"{speaker}:", current_word.word]
            last_speaker = speaker
        else:
            current_segment.append(current_word.word)

    if current_segment:
        all_segments.append(current_segment)

    all_sentences = [" ".join(segment) for segment in all_segments]
    all_sentences = [f"{i+1}. {sentence}" for i, sentence in enumerate(all_sentences)]
    return "\n".join(all_sentences)


def transcribe_and_combine_openai(user_audio_path, agent_audio_path):
    with TRANSCRIPTION_POOL as executor:
        user_future = executor.submit(transcribe_with_openai, user_audio_path)
        agent_future = executor.submit(transcribe_with_openai, agent_audio_path)

        _, user_words = user_future.result()
        _, agent_words = agent_future.result()

    return (
        create_combined_transcript(user_words, agent_words),
        user_words,
        agent_words,
    )


def transcribe_and_combine_deepgram(audio_path, user_channel="left"):
    _, user_words, _, agent_words = transcribe_with_deepgram(
        audio_path, user_channel
    )
    return (
        create_combined_transcript(user_words, agent_words),
        user_words,
        agent_words,
    )
