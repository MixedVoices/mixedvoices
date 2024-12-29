import os
from typing import Any, Dict, List, Optional
from uuid import uuid4

import mixedvoices
import mixedvoices.constants as constants
from mixedvoices.core.version import Version
from mixedvoices.evaluation.evaluator import Evaluator
from mixedvoices.utils import load_json, save_json, validate_name


def get_info_path(project_id):
    return os.path.join(constants.PROJECTS_FOLDER, project_id, "info.json")


class Project:
    def __init__(
        self,
        project_id: str,
        metric_names:List[str],
        evals: Optional[Dict[str, Evaluator]] = None,
    ):
        self.project_id = project_id
        self.metric_names = metric_names
        self.evals: Dict[str, Evaluator] = evals or {}
        self.save()

    def update_metric_names(self, metric_names: List[str]):
        self.metric_names = metric_names
        self.save()

    @property
    def project_folder(self):
        return os.path.join(constants.PROJECTS_FOLDER, self.project_id)

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
            "metric_names": self.metric_names,
        }
        save_json(d, self.path)

    @classmethod
    def load(cls, project_id):
        try:
            load_path = get_info_path(project_id)
            d = load_json(load_path)
            metric_names = d.pop("metric_names")
            eval_ids = d.pop("eval_ids")
            evals = {
                eval_id: Evaluator.load(project_id, eval_id) for eval_id in eval_ids
            }
            evals = {k: v for k, v in evals.items() if v}
            return cls(project_id, metric_names, evals)
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
        self, eval_prompts: List[str], metric_names: Optional[List[str]]
    ) -> Evaluator:
        """
        Create a new evaluator for the project

        Args:
            eval_prompts (List[str]): List of evaluation prompts, each acts as a separate test case
            metric_names (Optional[List[str]]): List of metric names to be evaluated, or None to use the metrics of the project.

        Returns:
            Evaluator: The newly created evaluator
        """  # noqa E501
        if isinstance(metric_names, list):
            mixedvoices.get_metrics(metric_names)  # checks existence
        elif metric_names is None:
            metric_names = self.metric_names.copy()
        else:
            raise ValueError("metric_names must be a list or None")

        eval_id = uuid4().hex
        cur_eval = Evaluator(
            eval_id,
            self.project_id,
            metric_names,
            eval_prompts,
        )

        self.evals[eval_id] = cur_eval
        self.save()
        return cur_eval
