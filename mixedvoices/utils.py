import os
from typing import TYPE_CHECKING, List

import librosa
import soundfile as sf

from mixedvoices.core.step import Step
from mixedvoices.processors.speech_analyzer import script_to_step_names
from mixedvoices.processors.transcriber import transcribe_and_combine

if TYPE_CHECKING:
    from mixedvoices.core.recording import Recording
    from mixedvoices.core.version import Version


def separate_channels(input_file, output_folder):
    """
    Separate stereo audio file into channels and save them as individual files.
    """
    # TODO: give user the ability to specify which channel assistant is speaking in
    y, sr = librosa.load(input_file, mono=False)

    if len(y.shape) != 2 or y.shape[0] != 2:
        raise ValueError("Input must be a stereo audio file")

    # Separate channels
    left_channel, right_channel = y[0], y[1]

    left_path = os.path.join(output_folder, "left.wav")
    right_path = os.path.join(output_folder, "right.wav")
    sf.write(left_path, left_channel, sr)
    sf.write(right_path, right_channel, sr)
    return left_path, right_path


def process_recording(recording: "Recording", version: "Version"):
    audio_path = recording.audio_path
    output_folder = os.path.join(version.path, "recordings", recording.recording_id)
    user_audio_path, assistant_audio_path = separate_channels(audio_path, output_folder)
    combined_transcript = transcribe_and_combine(user_audio_path, assistant_audio_path)
    recording.combined_transcript = combined_transcript
    existing_step_names = [step.name for step in version.steps.values()]
    step_names = script_to_step_names(combined_transcript, existing_step_names)

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
        step.record_usage(recording, is_final_step, False)
        step_options = step.next_steps
        previous_step = step

    for step in all_steps:
        step.save()
    recording.step_ids = [step.step_id for step in all_steps]
    recording.save()
