import json
import os
from typing import Any, Dict, Optional
from uuid import uuid4

import mixedvoices
import mixedvoices.constants as constants
from mixedvoices.core.recording import Recording
from mixedvoices.core.step import Step
from mixedvoices.evaluation.eval_case_generation import generate_eval_prompts
from mixedvoices.evaluation.evaluation_run import EvaluationRun
from mixedvoices.utils import process_recording


class Version:
    def __init__(
        self,
        version_id: str,
        project_id: str,
        prompt: str,
        success_criteria: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        evaluation_runs: Optional[Dict[str, EvaluationRun]] = None,
    ):
        self.version_id = version_id
        self.project_id = project_id
        self.prompt = prompt
        self.success_criteria = success_criteria
        self.metadata = metadata
        self.evaluation_runs = evaluation_runs or {}
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
        blocking: bool = True,
        metadata: Optional[Dict[str, Any]] = None,
        user_channel: str = "left",
    ):
        if self.success_criteria and is_successful is not None:
            raise ValueError(
                f"Version {self.version_id} already has success criteria set for automatic evaluation, cannot set is_successful"
            )
        recording_id = uuid4().hex
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
            process_recording(recording, self, user_channel)
        else:
            recording.processing_task_id = mixedvoices.TASK_MANAGER.add_task(
                "process_recording",
                recording=recording,
                version=self,
                user_channel=user_channel,
            )

        return recording

    def get_evaluation_run_ids(self):
        return list(self.evaluation_runs.keys())

    def save(self):
        save_path = os.path.join(self.path, "info.json")
        with open(save_path, "w") as f:
            d = {
                "prompt": self.prompt,
                "success_criteria": self.success_criteria,
                "metadata": self.metadata,
                "evaluation_run_ids": self.get_evaluation_run_ids(),
            }
            f.write(json.dumps(d))

    @classmethod
    def load(cls, project_id, version_id):
        load_path = os.path.join(
            constants.ALL_PROJECTS_FOLDER, project_id, version_id, "info.json"
        )
        with open(load_path, "r") as f:
            d = json.loads(f.read())
        prompt = d["prompt"]
        success_criteria = d.get("success_criteria", None)
        metadata = d.get("metadata", None)
        evaluation_run_ids = d.get("evaluation_run_ids", [])
        evaluation_runs = {
            run_id: EvaluationRun.load(project_id, version_id, run_id)
            for run_id in evaluation_run_ids
        }
        evaluation_runs = {k: v for k, v in evaluation_runs.items() if v}
        return cls(
            version_id,
            project_id,
            prompt,
            success_criteria,
            metadata,
            evaluation_runs,
        )

    def get_paths(self):
        # TODO implement
        return []

    def get_failure_reasons(self):
        # TODO implement
        return []

    def create_evaluation_run(
        self,
        empathy: bool = True,
        verbatim_repetition: bool = True,
        conciseness: bool = True,
        hallucination: bool = True,
        context_awareness: bool = True,
        scheduling: bool = True,
        adaptive_qa: bool = True,
        objection_handling: bool = True,
    ) -> EvaluationRun:
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
        all_paths = self.get_paths()
        all_failure_reasons = self.get_failure_reasons()
        print("Generating Evaluation Prompts")
        prompts = generate_eval_prompts(self.prompt, all_failure_reasons, all_paths)
        # print(prompts)

        run_id = uuid4().hex
        eval_run = EvaluationRun(
            run_id,
            self.project_id,
            self.version_id,
            self.prompt,
            metrics_dict,
            prompts,
        )

        self.evaluation_runs[run_id] = eval_run
        self.save()
        return eval_run
