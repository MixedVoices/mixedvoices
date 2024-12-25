import os
from functools import wraps

import numpy as np
import pytest
from scipy.io import wavfile


def needs_api_key(env_var):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not os.getenv(env_var):
                pytest.skip(f"{env_var} not found in environment")
            return func(*args, **kwargs)

        return wrapper

    return decorator


needs_openai_key = needs_api_key("OPENAI_API_KEY")
needs_deepgram_key = needs_api_key("DEEPGRAM_API_KEY")


def add_noise_to_audio(audio_file_path, output_path=None, noise_level=0.01):
    """
    Add Gaussian noise to a stereo audio file.

    Args:
        audio_file_path (str): Path to the input stereo audio file
        output_path (str): Path where to save the noisy audio file.
                          If None, will append '_noisy' to original filename
        noise_level (float): Standard deviation of the Gaussian noise (default: 0.01)

    Returns:
        str: Path to the noisy audio file
    """
    try:
        # Read the audio file
        sample_rate, audio_data = wavfile.read(audio_file_path)
        audio_data = audio_data.astype(float)

        # Normalize audio data to [-1, 1] range
        audio_data = audio_data / np.max(np.abs(audio_data))

        rng = np.random.default_rng()

        # Generate noise for both channels
        noise_left = rng.normal(0, noise_level, size=len(audio_data))
        noise_right = rng.normal(0, noise_level, size=len(audio_data))

        # Add noise to each channel
        noisy_left = audio_data[:, 0] + noise_left
        noisy_right = audio_data[:, 1] + noise_right

        # Combine channels back into stereo
        noisy_audio = np.column_stack((noisy_left, noisy_right))

        # Convert back to 16-bit PCM
        noisy_audio = (noisy_audio * 32767).astype(np.int16)

        # Determine output path
        if output_path is None:
            output_path = audio_file_path.replace(".wav", "_noisy.wav")

        # Save the noisy audio
        wavfile.write(output_path, sample_rate, noisy_audio)

        return output_path

    except Exception as e:
        print(f"Error adding noise to audio: {str(e)}")
        return None
