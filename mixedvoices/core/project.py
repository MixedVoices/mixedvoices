import os
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

import mixedvoices.constants as constants
from mixedvoices.core.version import Version
from mixedvoices.evaluation.evaluator import Evaluator
from mixedvoices.metrics.metric import Metric
from mixedvoices.utils import load_json, save_json, validate_name


def create_project(project_name: str, metrics: List[Metric]):
    """Create a new project"""
    validate_name(project_name, "project_name")
    check_metrics_while_adding(metrics)
    if project_name in os.listdir(constants.PROJECTS_FOLDER):
        raise ValueError(f"Project {project_name} already exists")
    os.makedirs(os.path.join(constants.PROJECTS_FOLDER, project_name))
    return Project(project_name, metrics)


def load_project(project_name: str):
    """Load an existing project"""
    if project_name not in os.listdir(constants.PROJECTS_FOLDER):
        raise ValueError(f"Project {project_name} does not exist")
    return Project.load(project_name)


def check_metrics_while_adding(
    metrics: List[Metric], existing_metrics: Optional[Dict[str, Metric]] = None
) -> List[Metric]:
    if not isinstance(metrics, list):
        metrics = [metrics]

    if not all(isinstance(metric, Metric) for metric in metrics):
        raise TypeError(
            "Metrics must be a list of Metric objects or a single Metric object"
        )
    if existing_metrics:
        for metric in metrics:
            if metric.name in existing_metrics:
                raise ValueError(
                    f"Metric with name '{metric.name}' already exists in project"
                )
    return metrics


def get_info_path(project_id):
    return os.path.join(constants.PROJECTS_FOLDER, project_id, "info.json")


class Project:
    def __init__(
        self,
        project_id: str,
        metrics: Optional[List[Metric]] = None,
        evals: Optional[Dict[str, Evaluator]] = None,
        _metrics: Optional[Dict[str, Metric]] = None,
    ):
        self.project_id = project_id
        self._metrics: Dict[str, Metric] = _metrics or {}
        self.evals: Dict[str, Evaluator] = evals or {}
        if metrics:
            self.add_metrics(metrics)

    def add_metrics(self, metrics: Union[Metric, List[Metric]]) -> None:
        """
        Add a new metrics to the project.
        Raises ValueError if metric with same name already exists.
        """
        metrics = check_metrics_while_adding(metrics, self._metrics)
        for metric in metrics:
            self._metrics[metric.name] = metric
        self.save()

    def update_metric(self, metric: Metric) -> None:
        """
        Update an existing metric.
        Raises KeyError if metric doesn't exist.
        """
        if metric.name not in self._metrics:
            raise KeyError(
                f"Metric with name '{metric.name}' does not exist in project"
            )
        self._metrics[metric.name] = metric
        self.save()

    def get_metric(self, metric_name: str) -> Metric:
        """
        Get a metric by name.
        Raises KeyError if metric doesn't exist.
        """
        if metric_name not in self._metrics:
            raise KeyError(
                f"Metric with name '{metric_name}' does not exist in project"
            )
        return self._metrics[metric_name]

    def get_metrics_by_names(self, metric_names: List[str]) -> List[Metric]:
        """
        Get multiple metrics by their names.
        Raises KeyError if any metric doesn't exist.
        """
        missing = [name for name in metric_names if name not in self._metrics]
        if missing:
            raise KeyError(f"Metrics not found in project: {', '.join(missing)}")
        return [self._metrics[name] for name in metric_names]

    def remove_metric(self, metric_name: str) -> None:
        """
        Remove a metric by name.
        Raises KeyError if metric doesn't exist.
        """
        if metric_name not in self._metrics:
            raise KeyError(
                f"Metric with name '{metric_name}' does not exist in project"
            )
        del self._metrics[metric_name]
        self.save()

    def list_metrics(self) -> List[Metric]:
        """Get all metrics as a list."""
        return list(self._metrics.values())

    def list_metric_names(self) -> List[str]:
        """Get all metric names."""
        return list(self._metrics.keys())

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
        metrics = {k: v.to_dict() for k, v in self._metrics.items()}
        d = {
            "eval_ids": list(self.evals.keys()),
            "metrics": metrics,
        }
        save_json(d, self.path)

    @classmethod
    def load(cls, project_id):
        try:
            load_path = get_info_path(project_id)
            d = load_json(load_path)
            metrics = d.pop("metrics")
            metrics = {
                k: Metric(name=k, definition=v["definition"], scoring=v["scoring"])
                for k, v in metrics.items()
            }
            eval_ids = d.pop("eval_ids")
            evals = {
                eval_id: Evaluator.load(project_id, eval_id) for eval_id in eval_ids
            }
            evals = {k: v for k, v in evals.items() if v}
            return cls(project_id, evals=evals, _metrics=metrics)
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
        self, eval_prompts: List[str], metric_names: Optional[List[str]] = None
    ) -> Evaluator:
        """
        Create a new evaluator for the project

        Args:
            eval_prompts (List[str]): List of evaluation prompts, each acts as a separate test case
            metrics (Optional[List[str]]): List of metric names to be evaluated, or None to use all project metrics.

        Returns:
            Evaluator: The newly created evaluator
        """  # noqa E501
        if metric_names is not None:
            self.get_metrics_by_names(metric_names)  # check for existence
        else:
            metric_names = self.list_metric_names()

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
