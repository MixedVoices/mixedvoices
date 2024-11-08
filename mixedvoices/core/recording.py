import json
import os
import time
from typing import List, Optional

from mixedvoices.constants import ALL_PROJECTS_FOLDER


class Recording:
    def __init__(
        self,
        recording_id: str,
        audio_path: str,
        version_id: str,
        project_id: str,
        created_at: Optional[int] = None,
        combined_transcript: Optional[str] = None,
        step_ids: Optional[List[str]] = None,
        summary: Optional[str] = None,
        is_successful: Optional[bool] = None,
    ):
        self.recording_id = recording_id
        self.created_at = created_at or int(time.time())
        self.audio_path = audio_path
        self.version_id = version_id
        self.project_id = project_id
        self.combined_transcript = combined_transcript
        self.step_ids = step_ids
        self.summary = summary
        self.is_successful = is_successful

    @property
    def path(self):
        return os.path.join(
            ALL_PROJECTS_FOLDER,
            self.project_id,
            self.version_id,
            "recordings",
            self.recording_id,
        )

    def save(self):
        os.makedirs(self.path, exist_ok=True)
        save_path = os.path.join(self.path, "info.json")
        with open(save_path, "w") as f:
            d = {
                "created_at": self.created_at,
                "audio_path": self.audio_path,
                "combined_transcript": self.combined_transcript,
                "step_ids": self.step_ids,
                "summary": self.summary,
                "is_successful": self.is_successful,
            }
            f.write(json.dumps(d))

    @classmethod
    def load(cls, project_id, version_id, recording_id):
        path = os.path.join(
            ALL_PROJECTS_FOLDER,
            project_id,
            version_id,
            "recordings",
            recording_id,
            "info.json",
        )
        with open(path, "r") as f:
            d = json.loads(f.read())

        d.update(
            {
                "project_id": project_id,
                "version_id": version_id,
                "recording_id": recording_id,
            }
        )
        return cls(**d)
