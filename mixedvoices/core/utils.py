import os
from concurrent import futures  # Preload this to avoid shutdown issues  # noqa: F401
from typing import TYPE_CHECKING, List

import joblib  # Preload joblib as well # noqa: F401
import librosa
import numpy as np
import soundfile as sf

from mixedvoices import constants
from mixedvoices.core.step import Step
from mixedvoices.processors.call_metrics import get_call_metrics
from mixedvoices.processors.llm_metrics import get_llm_metrics
from mixedvoices.processors.steps import script_to_step_names
from mixedvoices.processors.success import get_success
from mixedvoices.processors.summary import summarize_transcript
from mixedvoices.processors.transcriber import (
    transcribe_and_combine_deepgram,
    transcribe_and_combine_openai,
)

if TYPE_CHECKING:
    from mixedvoices.core.recording import Recording  # pragma: no cover
    from mixedvoices.core.version import Version  # pragma: no cover


def separate_channels(y: np.ndarray, sr: int, output_folder: str, user_channel="left"):
    """
    Separate stereo audio file into channels and save them as individual files.

    Parameters:
        y (numpy.ndarray): Audio data
        sr (int): Sample rate
        output_folder (str): Path to output folder
        user_channel (str): Channel containing user audio ("left" or "right")

    Returns:
        tuple: Paths to the saved channel files and audio duration
    """
    left_channel, right_channel = y[0], y[1]

    user_filename = "user.wav"
    assistant_filename = "assistant.wav"
    user_path = os.path.join(output_folder, user_filename)
    assistant_path = os.path.join(output_folder, assistant_filename)
    if user_channel == "left":
        sf.write(user_path, left_channel, sr)
        sf.write(assistant_path, right_channel, sr)
    else:
        sf.write(user_path, right_channel, sr)
        sf.write(assistant_path, left_channel, sr)
    return user_path, assistant_path


def get_transcript_and_duration(audio_path, output_folder, user_channel="left"):
    y, sr = librosa.load(audio_path, mono=False)
    duration = librosa.get_duration(y=y, sr=sr)
    if user_channel not in {"left", "right"}:
        raise ValueError('user_channel must be either "left" or "right"')
    if len(y.shape) != 2 or y.shape[0] != 2:
        raise ValueError("Input must be a stereo audio file")

    if constants.TRANSCRIPTION_PROVIDER == "openai":
        user_audio_path, assistant_audio_path = separate_channels(
            y, sr, output_folder, user_channel
        )
        combined_transcript, user_words, assistant_words = (
            transcribe_and_combine_openai(user_audio_path, assistant_audio_path)
        )
    elif constants.TRANSCRIPTION_PROVIDER == "deepgram":
        combined_transcript, user_words, assistant_words = (
            transcribe_and_combine_deepgram(audio_path, user_channel)
        )
    return combined_transcript, user_words, assistant_words, duration


def create_steps_from_names(
    step_names: List[str], version: "Version", recording: "Recording"
) -> List[Step]:
    all_steps: List[Step] = []
    step_options = version.starting_steps
    previous_step = None
    for i, step_name in enumerate(step_names):
        is_final_step = i == len(step_names) - 1
        step_option_names = [step.name for step in step_options]
        if step_name in step_option_names:
            step_index = step_option_names.index(step_name)
            step = step_options[step_index]
        else:
            step = Step(step_name, version.version_id, version.project_id)
            if previous_step is not None:
                step.previous_step_id = previous_step.step_id
                step.previous_step = previous_step
                previous_step.next_step_ids.append(step.step_id)
                previous_step.next_steps.append(step)
            version.steps[step.step_id] = step
        all_steps.append(step)
        step.record_usage(recording, is_final_step, recording.is_successful)
        step_options = step.next_steps
        previous_step = step
    for step in all_steps:
        step.save()
    return all_steps


def process_recording(recording: "Recording", version: "Version", user_channel="left"):
    try:
        audio_path = recording.audio_path
        output_folder = os.path.join(version.path, "recordings", recording.recording_id)
        combined_transcript, user_words, assistant_words, duration = (
            get_transcript_and_duration(audio_path, output_folder, user_channel)
        )
        recording.combined_transcript = (
            recording.combined_transcript or combined_transcript
        )
        if version.success_criteria:
            response = get_success(combined_transcript, version.success_criteria)
            recording.is_successful = response["success"]
            recording.success_explanation = response["explanation"]
        existing_step_names = [step.name for step in version.steps.values()]
        step_names = script_to_step_names(combined_transcript, existing_step_names)
        all_steps = create_steps_from_names(step_names, version, recording)
        recording.step_ids = [step.step_id for step in all_steps]
        recording.duration = duration
        recording.summary = recording.summary or summarize_transcript(
            combined_transcript
        )
        recording.llm_metrics = get_llm_metrics(combined_transcript, version.prompt)
        recording.call_metrics = get_call_metrics(
            audio_path, user_words, assistant_words, duration, user_channel
        )
        recording.task_status = "COMPLETED"
        recording.save()

    except Exception as e:
        recording.task_status = "FAILED"
        recording.save()
        raise e
