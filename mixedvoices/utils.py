import json

from openai import OpenAI

import mixedvoices


def get_openai_client():
    if mixedvoices.OPEN_AI_CLIENT is None:
        mixedvoices.OPEN_AI_CLIENT = OpenAI()
    return mixedvoices.OPEN_AI_CLIENT


def validate_name(name: str, identifier: str):
    allowed_special_chars = {"-", "_"}
    if (
        not all(c.isalnum() or c in allowed_special_chars for c in name)
        or len(name) == 0
    ):
        raise ValueError(
            f"{identifier} can only contain a-z, A-Z, 0-9, -, _ and must not be empty"
        )


def save_json(d, filename):
    with open(filename, "w") as f:
        f.write(json.dumps(d))


def load_json(filename):
    with open(filename, "r") as f:
        return json.loads(f.read())
