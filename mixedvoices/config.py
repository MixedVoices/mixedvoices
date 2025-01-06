# mixedvoices/config.py
import json
import os
from typing import Any, Dict

from mixedvoices.constants import MIXEDVOICES_FOLDER

# Define available options for specific fields
# If a field isn't listed here, any value is allowed
CONFIG_OPTIONS = {
    "TRANSCRIPTION_MODEL": ["openai/whisper-1", "deepgram/nova-2"],
}

DEFAULT_CONFIG = {
    "TRANSCRIPTION_MODEL": "openai/whisper-1",
    "METRICS_MODEL": "gpt-4o",
    "SUCCESS_MODEL": "gpt-4o",
    "SUMMARY_MODEL": "gpt-4o",
    "STEPS_MODEL": "gpt-4o",
    "EVAL_AGENT_MODEL": "gpt-4o",
    "TEST_CASE_GENERATOR_MODEL": "gpt-4o",
}

CONFIG_PATH = os.path.join(MIXEDVOICES_FOLDER, "config.json")


def ensure_config_exists():
    """Create config file with default values if it doesn't exist"""
    os.makedirs(MIXEDVOICES_FOLDER, exist_ok=True)

    if not os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "w") as f:
            json.dump(DEFAULT_CONFIG, f, indent=2)


def load_config() -> Dict[str, Any]:
    """Load configuration from file"""
    ensure_config_exists()
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)


def save_config(config: Dict[str, Any]):
    """Save configuration to file"""
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)


def update_value(key: str, new_value: str):
    """Update a specific key's value in the config"""
    config = load_config()
    if key not in config:
        raise ValueError(f"Invalid key name: {key}")

    # Validate against allowed options if they exist for this field
    if key in CONFIG_OPTIONS:
        if new_value not in CONFIG_OPTIONS[key]:
            raise ValueError(
                f"Invalid value for {key}. "
                f"Must be one of: {', '.join(CONFIG_OPTIONS[key])}"
            )

    config[key] = new_value
    save_config(config)


def get_value_from_config(key: str) -> str:
    """Get a specific key's value from the config"""
    config = load_config()
    return config.get(key, DEFAULT_CONFIG[key])
