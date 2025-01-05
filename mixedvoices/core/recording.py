import os
import time
from typing import Any, Dict, List, Optional

import mixedvoices.constants as constants
from mixedvoices.utils import load_json, save_json


def get_info_path(project_id, version_id, recording_id):
    return os.path.join(
        constants.PROJECTS_FOLDER,
        project_id,
        "versions",
        version_id,
        "recordings",
        recording_id,
        "info.json",
    )


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
        success_explanation: Optional[str] = None,
        duration: Optional[float] = None,
        processing_task_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        llm_metrics: Optional[Dict[str, Any]] = None,
        call_metrics: Optional[Dict[str, Any]] = None,
        task_status: Optional[str] = None,
    ):
        self._recording_id = recording_id
        self.created_at = created_at or int(time.time())
        self.audio_path = audio_path
        self.version_id = version_id
        self.project_id = project_id
        self.combined_transcript = combined_transcript
        self.step_ids = step_ids
        self.summary = summary
        self.is_successful = is_successful
        self.success_explanation = success_explanation
        self.duration = duration
        self.processing_task_id: Optional[str] = processing_task_id
        self.metadata = metadata or {}
        self.llm_metrics = llm_metrics or {}
        self.call_metrics = call_metrics or {}
        self.task_status = task_status or "Processing"

    @property
    def id(self):
        return self._recording_id

    @property
    def _path(self):
        return get_info_path(self.project_id, self.version_id, self.id)

    def _save(self):
        os.makedirs(os.path.dirname(self._path), exist_ok=True)
        d = self._to_dict()
        save_json(d, self._path)

    @classmethod
    def _load(cls, project_id, version_id, recording_id):
        path = get_info_path(project_id, version_id, recording_id)
        d = load_json(path)
        d.update(
            {
                "project_id": project_id,
                "version_id": version_id,
                "recording_id": recording_id,
            }
        )
        return cls(**d)

    def _to_dict(self):
        return {
            "created_at": self.created_at,
            "audio_path": self.audio_path,
            "combined_transcript": self.combined_transcript,
            "step_ids": self.step_ids,
            "summary": self.summary,
            "is_successful": self.is_successful,
            "success_explanation": self.success_explanation,
            "duration": self.duration,
            "processing_task_id": self.processing_task_id,
            "metadata": self.metadata,
            "task_status": self.task_status,
            "llm_metrics": self.llm_metrics,
            "call_metrics": self.call_metrics,
        }
