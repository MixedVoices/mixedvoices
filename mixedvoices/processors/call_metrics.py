from statistics import mean
from typing import List

import numpy as np
from openai.types.audio import TranscriptionWord
from scipy.io import wavfile


def calculate_stereo_snr(audio_file_path, user_channel="left"):
    """
    Calculate SNR for both channels of a stereo audio file.
    Uses first 1000 samples for noise measurement.

    Args:
        audio_file_path (str): Path to the stereo audio file

    Returns:
        tuple: (user_channel_snr, agent_channel_snr)
    """
    try:
        _, audio_data = wavfile.read(audio_file_path)
        audio_data = audio_data.astype(float)
        left_channel = audio_data[:, 0]
        right_channel = audio_data[:, 1]

        results = []
        for channel in [left_channel, right_channel]:
            signal_rms = np.sqrt(np.mean(channel**2))  # Calculate RMS of full signal
            noise_sample = channel[:1000]  # Use first 1000 samples for noise
            noise_rms = np.sqrt(np.mean(noise_sample**2))
            if noise_rms > 0:
                snr = 20 * np.log10(signal_rms / noise_rms)
                results.append(f"{round(snr, 2)} dB")
            else:
                results.append("N/A")

        if user_channel == "left":
            return results[0], results[1]
        else:
            return results[1], results[0]
    except Exception:
        print("Error calculating SNR")
        return "N/A", "N/A"


def calculate_wpm(agent_words: List[TranscriptionWord]) -> float:
    """
    Calculate the average Words Per Minute (WPM).

    Args:
        words (List[TranscriptionWord]): List of TranscriptionWord objects

    Returns:
        float: Average WPM
    """
    try:
        segments = []
        current_segment = None

        for word in agent_words:
            if current_segment is None:
                current_segment = {"start": word.start, "end": word.end, "words": 1}
            else:
                # If words are close (<1 second gap), consider them same segment
                if word.start - current_segment["end"] < 1.0:
                    current_segment["end"] = word.end
                    current_segment["words"] += 1
                else:
                    segments.append(current_segment)
                    current_segment = {"start": word.start, "end": word.end, "words": 1}

        if current_segment is not None:
            segments.append(current_segment)

        if not segments:
            return 0.0

        total_words = sum(segment["words"] for segment in segments)
        total_duration = sum(segment["end"] - segment["start"] for segment in segments)

        return total_words / (total_duration / 60)
    except Exception:
        print("Error calculating WPM")
        return "N/A"


def group_utterances(words: List[TranscriptionWord]) -> List[List[TranscriptionWord]]:
    if not words:
        return []

    utterances = []
    current_utterance = [words[0]]

    for word in words[1:]:
        if word.start - current_utterance[-1].end > 1.0:
            utterances.append(current_utterance)
            current_utterance = [word]
        else:
            current_utterance.append(word)

    utterances.append(current_utterance)
    return utterances


def calculate_latency_and_interruptions(
    user_words: List[TranscriptionWord],
    agent_words: List[TranscriptionWord],
    duration: float,
    interruption_threshold: float = 0.2,
) -> dict:
    """
    Calculate agent response latency and identify interruptions using a single pass.

    Args:
        user_words: List of user TranscriptionWord objects
        agent_words: List of agent TranscriptionWord objects
        duration: Total duration of the call in seconds
        interruption_threshold: Threshold in seconds below which a response is considered an interruption

    Returns:
        Dictionary containing latency statistics and interruption data
    """
    try:
        user_utterances = group_utterances(user_words)
        agent_utterances = group_utterances(agent_words)

        latencies = []
        user_interruptions = 0
        agent_interruptions = 0

        i, j = 0, 0  # Pointers for user and agent utterances

        while i < len(user_utterances) and j < len(agent_utterances):
            user_utt = user_utterances[i]
            agent_utt = agent_utterances[j]

            user_start, user_end = user_utt[0].start, user_utt[-1].end
            asst_start, asst_end = agent_utt[0].start, agent_utt[-1].end

            # Check for overlaps and calculate latencies
            if asst_start < user_start < asst_end:
                user_interruptions += 1
                i += 1
            elif user_start < asst_start < user_end:
                agent_interruptions += 1
                j += 1
            else:
                # No overlap - check if it's a normal response
                if asst_start > user_end:
                    if asst_start - user_end >= interruption_threshold:
                        latencies.append(asst_start - user_end)
                    i += 1
                else:
                    j += 1

        return {
            "average_latency": mean(latencies) if latencies else 0,
            "user_interruptions_per_minute": user_interruptions / (duration / 60),
            "agent_interruptions_per_minute": agent_interruptions
            / (duration / 60),
        }

    except Exception:
        print("Error calculating latency and interruptions")
        return {
            "average_latency": "N/A",
            "user_interruptions_per_minute": "N/A",
            "agent_interruptions_per_minute": "N/A",
        }


def get_call_metrics(
    audio_file_path, user_words, agent_words, duration, user_channel="left"
):
    stereo_snr = calculate_stereo_snr(audio_file_path, user_channel)
    wpm = calculate_wpm(agent_words)
    res = calculate_latency_and_interruptions(user_words, agent_words, duration)
    res["user_snr"] = stereo_snr[0]
    res["agent_snr"] = stereo_snr[1]
    res["wpm"] = wpm
    return res
