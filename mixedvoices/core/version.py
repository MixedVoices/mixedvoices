import os
from typing import Any, Dict, List, Optional
from uuid import uuid4
from warnings import warn

import mixedvoices
import mixedvoices.constants as constants
from mixedvoices.core import utils
from mixedvoices.core.recording import Recording
from mixedvoices.core.step import Step
from mixedvoices.core.task_manager import TASK_MANAGER
from mixedvoices.utils import load_json, save_json


def dfs(
    current_step: Step,
    current_path: list[Step],
    all_paths: List[str],
):
    current_path.append(current_step)

    if not current_step.next_steps:  # leaf node => complete path
        current_path_names = [step.name for step in current_path]
        current_path_str = "->".join(current_path_names)
        all_paths.append(current_path_str)
    else:
        for next_step in current_step.next_steps:
            dfs(next_step, current_path, all_paths)

    current_path.pop()  # Backtrack


def get_info_path(project_id, version_id):
    return os.path.join(
        constants.PROJECTS_FOLDER, project_id, "versions", version_id, "info.json"
    )


class Version:
    def __init__(
        self,
        version_id: str,
        project_id: str,
        prompt: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.version_id = version_id
        self.project_id = project_id
        self._prompt = prompt
        self._metadata = metadata
        self._load_recordings()
        self._load_steps()
        self._create_flowchart()
        self._all_step_names = None
        self._cached_project = None

    @property
    def prompt(self):
        """Get the prompt of the version"""
        return self._prompt

    @property
    def recording_count(self):
        return len(self._recordings)

    def get_recording(self, recording_id: str):
        if recording_id not in self._recordings:
            raise ValueError(
                f"Recording {recording_id} not found in version {self.version_id}"
            )
        return self._recordings[recording_id]

    def update_prompt(self, prompt: str):
        """Update the prompt of the version"""
        self._prompt = prompt
        self._save()

    @property
    def metadata(self):
        """Get the metadata of the version"""
        return self._metadata

    def update_metadata(self, metadata: Dict[str, Any]):
        """Update the metadata of the version"""
        self._metadata = metadata
        self._save()

    def add_recording(
        self,
        audio_path: str,
        user_channel: str = "left",
        is_successful: Optional[bool] = None,
        blocking: bool = True,
        transcript: Optional[str] = None,
        summary: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Add a recording to the version

        Args:
            audio_path (str): Path to the audio file, should be a stereo recording with user and agent on separate channels
            user_channel (str): Audio channel of the user, either "left" or "right". Defaults to "left".
            is_successful (Optional[bool]): If the recording is successful or not Defaults to None.
              This will override the automatic successs classification if project has success criteria
            blocking (bool): If True, block until recording is processed, otherwise adds to queue and processes in the background. Defaults to True.
            transcript (Optional[str]): Transcript of the recording, this overrides the transcript generated during analysis. Defaults to None.
              This doesn't stop the transcription, as that generates more granular transcript with timestamps.
            summary (Optional[str]): Summary of the recording, this overrides the summary generated during analysis. Defaults to None.
              This prevents summary from being generated during analysis.
            metadata (Optional[Dict[str, Any]]): Metadata to be associated with the recording. Defaults to None.
        """  # noqa E501
        if self._project._success_criteria and is_successful is not None:
            warn(
                "is_successful specified for a project with success criteria set. Overriding automatic success classification.",
                UserWarning,
                stacklevel=2,
            )
        if user_channel not in ["left", "right"]:
            raise ValueError(
                f"User channel must be either 'left' or 'right', got {user_channel}"
            )
        recording_id = uuid4().hex
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio path {audio_path} does not exist")

        extension = os.path.splitext(audio_path)[1]
        file_name = os.path.basename(audio_path)
        if extension not in [".mp3", ".wav"]:
            raise ValueError(f"Audio path {audio_path} is not an mp3 or wav file")

        output_folder = os.path.join(self._recordings_path, recording_id)
        output_audio_path = os.path.join(output_folder, file_name)
        os.makedirs(output_folder)
        os.system(f"cp {audio_path} {output_audio_path}")

        recording = Recording(
            recording_id,
            output_audio_path,
            self.version_id,
            self.project_id,
            is_successful=is_successful,
            combined_transcript=transcript,
            summary=summary,
            metadata=metadata,
        )
        self._recordings[recording.recording_id] = recording
        recording.save()

        if blocking:
            utils.process_recording(recording, self, user_channel)
        else:
            recording.processing_task_id = TASK_MANAGER.add_task(
                "process_recording",
                recording=recording,
                version=self,
                user_channel=user_channel,
            )

    def _save(self):
        d = {
            "prompt": self._prompt,
            "metadata": self._metadata,
        }
        save_json(d, self._path)

    @classmethod
    def _load(cls, project_id, version_id):
        load_path = get_info_path(project_id, version_id)
        d = load_json(load_path)
        prompt = d["prompt"]
        metadata = d.get("metadata", None)
        return cls(
            version_id,
            project_id,
            prompt,
            metadata,
        )

    @property
    def _project(self):
        if self._cached_project is None:
            self._cached_project = mixedvoices.load_project(self.project_id)
        return self._cached_project

    @property
    def _path(self):
        return get_info_path(self.project_id, self.version_id)

    @property
    def _recordings_path(self):
        return os.path.join(os.path.dirname(self._path), "recordings")

    @property
    def _steps_path(self):
        return os.path.join(os.path.dirname(self._path), "steps")

    def _load_recordings(self):
        self._recordings: Dict[str, Recording] = {}
        recording_files = os.listdir(self._recordings_path)
        for recording_file in recording_files:
            try:
                filename = os.path.basename(recording_file)
                recording_id = os.path.splitext(filename)[0]
                self._recordings[recording_id] = Recording.load(
                    self.project_id, self.version_id, recording_id
                )
            except Exception as e:
                print(f"Error loading recording {recording_file}: {e}")

    def _load_steps(self):
        self.steps: Dict[str, Step] = {}
        step_files = os.listdir(self._steps_path)
        for step_file in step_files:
            filename = os.path.basename(step_file)
            step_id = os.path.splitext(filename)[0]
            self.steps[step_id] = Step.load(self.project_id, self.version_id, step_id)

    @property
    def _starting_steps(self):
        return [step for step in self.steps.values() if step.previous_step_id is None]

    def _create_flowchart(self):
        for starting_step in self._starting_steps:
            self._recursively_assign_steps(starting_step)

    def _recursively_assign_steps(self, step: Step):
        step.next_steps = [
            self.steps[next_step_id] for next_step_id in step.next_step_ids
        ]
        step.previous_step = (
            self.steps[step.previous_step_id]
            if step.previous_step_id is not None
            else None
        )
        for next_step in step.next_steps:
            self._recursively_assign_steps(next_step)

    def _get_paths(self) -> List[str]:
        """
        Returns all possible paths through the conversation flow using DFS.
        Each path is a list of Step objects representing a complete conversation path.

        Returns:
            List[str]: List of all possible paths through the conversation
        """

        all_paths = []
        for start_step in self._starting_steps:
            dfs(start_step, [], all_paths)

        return all_paths

    def _get_step_names(self) -> List[str]:
        return list({step.name for step in self.steps.values()})
