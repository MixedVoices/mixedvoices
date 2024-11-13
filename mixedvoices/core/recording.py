import json
import os
import time
from typing import Any, Dict, List, Optional

import mixedvoices.constants as constants


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
        duration: Optional[float] = None,
        processing_task_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
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
        self.duration = duration
        self.processing_task_id: Optional[str] = processing_task_id
        self.metadata = metadata or {}

    @property
    def path(self):
        return os.path.join(
            constants.ALL_PROJECTS_FOLDER,
            self.project_id,
            self.version_id,
            "recordings",
            self.recording_id,
        )

    def save(self):
        os.makedirs(self.path, exist_ok=True)
        save_path = os.path.join(self.path, "info.json")
        with open(save_path, "w") as f:
            d = self.to_dict()
            f.write(json.dumps(d))

    def get_summary_from_metadata(self):
        analysis_info = self.metadata.get("analysis_info", {})
        summary = analysis_info.get("summary", None)
        if summary:
            return summary

    def get_combined_transcript_from_metadata(self):
        call_info = self.metadata.get("call_info", {})
        combined_transcript = call_info.get("transcript", None)
        if combined_transcript:
            return combined_transcript

    @classmethod
    def load(cls, project_id, version_id, recording_id):
        path = os.path.join(
            constants.ALL_PROJECTS_FOLDER,
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

    def to_dict(self):
        return {
            "created_at": self.created_at,
            "audio_path": self.audio_path,
            "combined_transcript": self.combined_transcript,
            "step_ids": self.step_ids,
            "summary": self.summary,
            "is_successful": self.is_successful,
            "duration": self.duration,
            "processing_task_id": self.processing_task_id,
            "metadata": self.metadata,
        }
