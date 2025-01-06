import os
from typing import TYPE_CHECKING, Optional
from uuid import uuid4

import mixedvoices.constants as constants
from mixedvoices.utils import load_json, save_json

if TYPE_CHECKING:
    from mixedvoices.core.recording import Recording  # pragma: no cover


def get_info_path(project_id, version_id, step_id):
    return os.path.join(
        constants.PROJECTS_FOLDER,
        project_id,
        "versions",
        version_id,
        "steps",
        step_id,
        "info.json",
    )


class Step:
    def __init__(
        self,
        name,
        version_id,
        project_id,
        recording_ids: Optional[list] = None,
        number_of_terminated_calls: int = 0,
        number_of_failed_calls: int = 0,
        previous_step_id: Optional[str] = None,
        next_step_ids: Optional[list] = None,
        step_id: Optional[str] = None,
    ):
        self.step_id = step_id or uuid4().hex
        self.name = name
        self.version_id = version_id
        self.project_id = project_id
        self.recording_ids = recording_ids or []
        self.number_of_terminated_calls = number_of_terminated_calls
        self.number_of_failed_calls = number_of_failed_calls
        self.previous_step_id = previous_step_id
        self.next_step_ids = next_step_ids or []
        self.previous_step = None
        self.next_steps = []

    @property
    def number_of_calls(self):
        return len(self.recording_ids)

    @property
    def path(self):
        return get_info_path(self.project_id, self.version_id, self.step_id)

    def record_usage(self, recording: "Recording", is_final_step, is_successful):
        self.recording_ids.append(recording.id)
        if is_final_step and not is_successful:
            self.number_of_failed_calls += 1

    def save(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        d = {
            "name": self.name,
            "recording_ids": self.recording_ids,
            "number_of_terminated_calls": self.number_of_terminated_calls,
            "number_of_failed_calls": self.number_of_failed_calls,
            "previous_step_id": self.previous_step_id,
            "next_step_ids": self.next_step_ids,
        }
        save_json(d, self.path)

    @classmethod
    def load(cls, project_id, version_id, step_id):
        path = get_info_path(project_id, version_id, step_id)
        d = load_json(path)
        d.update(
            {"project_id": project_id, "version_id": version_id, "step_id": step_id}
        )
        return cls(**d)
