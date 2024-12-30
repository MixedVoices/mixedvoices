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
    return os.path.join(constants.PROJECTS_FOLDER, project_id, version_id, "info.json")


class Version:
    def __init__(
        self,
        version_id: str,
        project_id: str,
        prompt: str,
        success_criteria: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.version_id = version_id
        self.project_id = project_id
        self.prompt = prompt
        self.success_criteria = success_criteria
        self.metadata = metadata
        self.load_recordings()
        self.load_steps()
        self.create_flowchart()
        self._all_step_names = None
        self._project = None

    @property
    def project(self):
        if self._project is None:
            self._project = mixedvoices.load_project(self.project_id)
        return self._project

    @property
    def path(self):
        return get_info_path(self.project_id, self.version_id)

    @property
    def recordings_path(self):
        return os.path.join(os.path.dirname(self.path), "recordings")

    @property
    def steps_path(self):
        return os.path.join(os.path.dirname(self.path), "steps")

    def load_recordings(self):
        self.recordings: Dict[str, Recording] = {}
        recording_files = os.listdir(self.recordings_path)
        for recording_file in recording_files:
            try:
                filename = os.path.basename(recording_file)
                recording_id = os.path.splitext(filename)[0]
                self.recordings[recording_id] = Recording.load(
                    self.project_id, self.version_id, recording_id
                )
            except Exception as e:
                print(f"Error loading recording {recording_file}: {e}")

    def load_steps(self):
        self.steps: Dict[str, Step] = {}
        step_files = os.listdir(self.steps_path)
        for step_file in step_files:
            filename = os.path.basename(step_file)
            step_id = os.path.splitext(filename)[0]
            self.steps[step_id] = Step.load(self.project_id, self.version_id, step_id)

    @property
    def starting_steps(self):
        return [step for step in self.steps.values() if step.previous_step_id is None]

    def create_flowchart(self):
        for starting_step in self.starting_steps:
            self.recursively_assign_steps(starting_step)

    def recursively_assign_steps(self, step: Step):
        step.next_steps = [
            self.steps[next_step_id] for next_step_id in step.next_step_ids
        ]
        step.previous_step = (
            self.steps[step.previous_step_id]
            if step.previous_step_id is not None
            else None
        )
        for next_step in step.next_steps:
            self.recursively_assign_steps(next_step)

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
              This will override the automatic successs classification if version has success criteria
            blocking (bool): If True, block until recording is processed, otherwise adds to queue and processes in the background. Defaults to True.
            transcript (Optional[str]): Transcript of the recording, this overrides the transcript generated during analysis. Defaults to None.
              This doesn't stop the transcription, as that generates more granular transcript with timestamps.
            summary (Optional[str]): Summary of the recording, this overrides the summary generated during analysis. Defaults to None.
              This prevents summary from being generated during analysis.
            metadata (Optional[Dict[str, Any]]): Metadata to be associated with the recording. Defaults to None.
        """  # noqa E501
        if self.success_criteria and is_successful is not None:
            warn(
                "is_successful specified for a version with success criteria set. Overriding automatic success classification.",
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

        output_folder = os.path.join(self.recordings_path, recording_id)
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
        self.recordings[recording.recording_id] = recording
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

        return recording

    def save(self):
        d = {
            "prompt": self.prompt,
            "success_criteria": self.success_criteria,
            "metadata": self.metadata,
        }
        save_json(d, self.path)

    @classmethod
    def load(cls, project_id, version_id):
        load_path = get_info_path(project_id, version_id)
        d = load_json(load_path)
        prompt = d["prompt"]
        success_criteria = d.get("success_criteria", None)
        metadata = d.get("metadata", None)
        return cls(
            version_id,
            project_id,
            prompt,
            success_criteria,
            metadata,
        )

    def get_paths(self):
        """
        Returns all possible paths through the conversation flow using DFS.
        Each path is a list of Step objects representing a complete conversation path.

        Returns:
            List[str]: List of all possible paths through the conversation
        """

        all_paths = []
        for start_step in self.starting_steps:
            dfs(start_step, [], all_paths)

        return all_paths

    def get_failure_reasons(self):
        # TODO implement
        return []

    def get_step_names(self):
        return list({step.name for step in self.steps.values()})

    def get_project_step_names(self):
        # TODO optimize
        return self.project.get_step_names()

    def get_project_metrics(self):
        return self.project.list_metrics()
