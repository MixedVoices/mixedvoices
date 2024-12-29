import os
from typing import Any, Dict, List, Optional
from uuid import uuid4

import mixedvoices.constants as constants
from mixedvoices.core.version import Version
from mixedvoices.evaluation.evaluator import Evaluator
from mixedvoices.metrics import Metric, deserialize_metrics, serialize_metrics
from mixedvoices.utils import load_json, save_json, validate_name


def get_info_path(project_id):
    return os.path.join(constants.ALL_PROJECTS_FOLDER, project_id, "info.json")


class Project:
    def __init__(
        self,
        project_id: str,
        metrics: Optional[List[Metric]] = None,
        evals: Optional[Dict[str, Evaluator]] = None,
    ):
        self.project_id = project_id
        self.metrics = metrics
        self.evals: Dict[str, Evaluator] = evals or {}
        self.save()

    def update_metrics(self, metrics: List[Metric]):
        self.metrics = metrics
        self.save()

    @property
    def project_folder(self):
        return os.path.join(constants.ALL_PROJECTS_FOLDER, self.project_id)

    @property
    def versions(self):
        all_files = os.listdir(self.project_folder)
        return [
            f for f in all_files if os.path.isdir(os.path.join(self.project_folder, f))
        ]

    @property
    def path(self):
        return get_info_path(self.project_id)

    def save(self):
        d = {
            "eval_ids": list(self.evals.keys()),
            "metrics": serialize_metrics(self.metrics),
        }
        save_json(d, self.path)

    @classmethod
    def load(cls, project_id):
        try:
            load_path = get_info_path(project_id)
            d = load_json(load_path)
            metrics = deserialize_metrics(d.pop("metrics"))

            eval_ids = d.pop("eval_ids")
            evals = {
                eval_id: Evaluator.load(project_id, eval_id) for eval_id in eval_ids
            }
            evals = {k: v for k, v in evals.items() if v}
            return cls(project_id, metrics, evals)
        except FileNotFoundError:
            return cls(project_id)

    def create_version(
        self,
        version_id: str,
        prompt: str,
        success_criteria: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Create a new version in the project

        Args:
            version_id (str): Name of the version
            prompt (str): Prompt used by the voice agent
            success_criteria (Optional[str]): Success criteria for the version. Used to automatically determine if a recording is successful or not. Defaults to None.
            metadata (Optional[Dict[str, Any]]): Metadata to be associated with the version. Defaults to None.
        """  # noqa E501
        validate_name(version_id, "version_id")
        if version_id in self.versions:
            raise ValueError(f"Version {version_id} already exists")
        version_folder = os.path.join(self.project_folder, version_id)
        os.makedirs(version_folder)
        os.makedirs(os.path.join(version_folder, "recordings"))
        os.makedirs(os.path.join(version_folder, "steps"))
        version = Version(
            version_id, self.project_id, prompt, success_criteria, metadata
        )
        version.save()
        return version

    def load_version(self, version_id: str):
        if version_id not in self.versions:
            raise ValueError(f"Version {version_id} does not exist")
        return Version.load(self.project_id, version_id)

    def get_paths(self):
        paths = []
        for version_id in self.versions:
            version = self.load_version(version_id)
            paths.extend(version.get_paths())
        return paths

    def get_step_names(self):
        step_names = []
        for version_id in self.versions:
            version = self.load_version(version_id)
            step_names.extend(version.get_step_names())
        return step_names

    def create_evaluator(
        self, eval_prompts: List[str], metrics: List["Metric"]
    ) -> Evaluator:
        """
        Create a new evaluator for the project

        Args:
            eval_prompts (List[str]): List of evaluation prompts, each acts as a separate test case
            metrics (List[Metric]): List of metrics to be evaluated

        Returns:
            Evaluator: The newly created evaluator
        """  # noqa E501
        eval_id = uuid4().hex
        cur_eval = Evaluator(
            eval_id,
            self.project_id,
            metrics,
            eval_prompts,
        )

        self.evals[eval_id] = cur_eval
        self.save()
        return cur_eval
