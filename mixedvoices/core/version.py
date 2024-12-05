import json
import os
from typing import Any, Dict, Iterator, Optional
from uuid import uuid4

import mixedvoices.constants as constants
from enterprise.eval_case_generation import create_prompt_runs
from mixedvoices.core.eval_prompt_run import EvalPromptRun
from mixedvoices.core.project import Project
from mixedvoices.core.recording import Recording
from mixedvoices.core.step import Step
from mixedvoices.core.task_manager import TaskManager
from mixedvoices.utils import process_recording


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
        self.prompt = prompt
        self.metadata = metadata
        self.task_manager = TaskManager()
        self.load_recordings()
        self.load_steps()
        self.create_flowchart()

    @property
    def path(self):
        return os.path.join(
            constants.ALL_PROJECTS_FOLDER, self.project_id, self.version_id
        )

    def load_recordings(self):
        self.recordings: Dict[str, Recording] = {}
        recordings_path = os.path.join(self.path, "recordings")
        recording_files = os.listdir(recordings_path)
        for recording_file in recording_files:
            filename = os.path.basename(recording_file)
            recording_id = os.path.splitext(filename)[0]
            self.recordings[recording_id] = Recording.load(
                self.project_id, self.version_id, recording_id
            )

    def load_steps(self):
        self.steps: Dict[str, Step] = {}
        steps_path = os.path.join(self.path, "steps")
        step_files = os.listdir(steps_path)
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
        is_successful: Optional[bool] = None,
        blocking: bool = False,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        recording_id = str(uuid4())
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio path {audio_path} does not exist")

        extension = os.path.splitext(audio_path)[1]
        file_name = os.path.basename(audio_path)
        if extension not in [".mp3", ".wav"]:
            raise ValueError(f"Audio path {audio_path} is not an mp3 or wav file")

        output_folder = os.path.join(self.path, "recordings", recording_id)
        output_audio_path = os.path.join(output_folder, file_name)
        os.makedirs(output_folder)
        os.system(f"cp {audio_path} {output_audio_path}")

        recording = Recording(
            recording_id,
            output_audio_path,
            self.version_id,
            self.project_id,
            is_successful=is_successful,
            metadata=metadata,
        )
        self.recordings[recording.recording_id] = recording
        recording.save()

        if blocking:
            process_recording(recording, self)
        else:
            task_id = self.task_manager.add_task(
                "process_recording", recording=recording, version=self
            )
            recording.processing_task_id = task_id

        return recording

    def save(self):
        save_path = os.path.join(self.path, "info.json")
        with open(save_path, "w") as f:
            d = {"prompt": self.prompt, "metadata": self.metadata}
            f.write(json.dumps(d))

    @classmethod
    def load(cls, project_id, version_id):
        load_path = os.path.join(
            constants.ALL_PROJECTS_FOLDER, project_id, version_id, "info.json"
        )
        with open(load_path, "r") as f:
            d = json.loads(f.read())
        return cls(version_id, project_id, d["prompt"], d["metadata"])

    def get_paths(self):
        # TODO implement
        pass

    def get_failure_reasons(self):
        # TODO implement
        pass

    def create_evaluator(
        self,
        use_recordings_from_other_versions: bool = False,  # TODO: Create separate methods
        empathy: bool = True,
        verbatim_repetition: bool = True,
        conciseness: bool = True,
        hallucination: bool = True,
        context_awareness: bool = True,
        scheduling: bool = True,
        adaptive_qa: bool = True,
        objection_handling: bool = True,
    ) -> Iterator[EvalPromptRun]:
        metrics_dict = {
            "empathy": empathy,
            "verbatim_repetition": verbatim_repetition,
            "conciseness": conciseness,
            "hallucination": hallucination,
            "context_awareness": context_awareness,
            "scheduling": scheduling,
            "adaptive_qa": adaptive_qa,
            "objection_handling": objection_handling,
        }
        if use_recordings_from_other_versions:
            project = Project(self.project_id)
            all_paths = project.get_paths()
            all_failure_reasons = project.get_failure_reasons()
        else:
            all_paths = self.get_paths()
            all_failure_reasons = self.get_failure_reasons()

        prompt_run_ids = create_prompt_runs(
            self.project_id,
            self.version_id,
            self.prompt,
            use_recordings_from_other_versions,
            metrics_dict,
            all_paths,
            all_failure_reasons,
        )

        for prompt_run_id in prompt_run_ids:
            yield EvalPromptRun(self, prompt_run_id)

    def get_fixed_prompt(self):
        # check mixedvoices token
        # get fixed prompt from server
        pass

    def get_prompt_suggestions(self):
        # check mixedvoices token
        # get prompt suggestions from server
        pass
