from typing import List

from openai import OpenAI
from openai.types.audio import TranscriptionVerbose, TranscriptionWord

import mixedvoices


def transcribe_with_whisper(audio_path):
    # TODO: Remove long silences from script before
    # sending to whisper to speed up transcription and reduce cost
    # later adjust the time stamps according to silences
    if mixedvoices.OPEN_AI_CLIENT is None:
        mixedvoices.OPEN_AI_CLIENT = OpenAI()

    client = mixedvoices.OPEN_AI_CLIENT
    with open(audio_path, "rb") as audio_file:
        json_response: TranscriptionVerbose = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="verbose_json",
            timestamp_granularities=["word"],
        )

    assert json_response.words is not None
    return json_response.text, json_response.words


def create_combined_transcript(
    user_words: List[TranscriptionWord], assistant_words: List[TranscriptionWord]
):
    last_speaker = None
    user_index, assistant_index = 0, 0
    all_segments = []
    current_segment = []
    while user_index < len(user_words) or assistant_index < len(assistant_words):
        user_word = user_words[user_index] if user_index < len(user_words) else None
        assistant_word = (
            assistant_words[assistant_index]
            if assistant_index < len(assistant_words)
            else None
        )

        if not assistant_word or (user_word and user_word.start < assistant_word.start):
            speaker = "user"
            current_word = user_word
            user_index += 1
        else:
            speaker = "bot"
            current_word = assistant_word
            assistant_index += 1

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
    return "\n".join(all_sentences)


def transcribe_and_combine(user_audio_path, assistant_audio_path):
    _, user_words = transcribe_with_whisper(user_audio_path)
    _, assistant_words = transcribe_with_whisper(assistant_audio_path)
    return create_combined_transcript(user_words, assistant_words)
