import os
from typing import Any, Dict, List, Optional
from uuid import uuid4

import mixedvoices.constants as constants
from mixedvoices.core.version import Version
from mixedvoices.evaluation.evaluator import Evaluator
from mixedvoices.metrics.metric import Metric
from mixedvoices.utils import load_json, save_json, validate_name


def create_project(
    project_id: str, metrics: List[Metric], success_criteria: Optional[str] = None
):
    """Create a new project

    Args:
        project_id (str): Name of the project
        metrics (List[Metric]): List of metrics to be added to the project
        success_criteria (Optional[str]): Success criteria for the version. Used to automatically determine if a recording is successful or not. Defaults to None.
    """
    validate_name(project_id, "project_id")
    check_metrics_while_adding(metrics)
    if project_id in os.listdir(constants.PROJECTS_FOLDER):
        raise FileExistsError(f"Project {project_id} already exists")
    os.makedirs(os.path.join(constants.PROJECTS_FOLDER, project_id))
    return Project(project_id, metrics, success_criteria)


def load_project(project_id: str):
    """Load an existing project"""
    if project_id not in os.listdir(constants.PROJECTS_FOLDER):
        raise KeyError(f"Project {project_id} does not exist")
    return Project._load(project_id)


def check_metrics_while_adding(
    metrics: List[Metric], existing_metrics: Optional[Dict[str, Metric]] = None
) -> List[Metric]:
    if not all(isinstance(metric, Metric) for metric in metrics):
        raise TypeError("Metrics must be a list of Metric objects")
    if existing_metrics:
        for metric in metrics:
            if metric.name in existing_metrics:
                raise FileExistsError(
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
        success_criteria: Optional[str] = None,
        evals: Optional[Dict[str, Evaluator]] = None,
        _metrics: Optional[Dict[str, Metric]] = None,
    ):
        self._project_id = project_id
        self._success_criteria = success_criteria
        self._metrics: Dict[str, Metric] = _metrics or {}
        self._evals: Dict[str, Evaluator] = evals or {}
        os.makedirs(os.path.join(self._project_folder, "versions"), exist_ok=True)
        if metrics:
            self.add_metrics(metrics)
        else:
            self._save()

    @property
    def id(self) -> str:
        """Get the name of the project"""
        return self._project_id

    # Metric methods
    @property
    def metrics(self) -> List[Metric]:
        """Get all metrics in the project"""
        return list(self._metrics.values())

    def add_metrics(self, metrics: List[Metric]) -> None:
        """
        Add new metrics to the project.
        """
        metrics = check_metrics_while_adding(metrics, self._metrics)
        for metric in metrics:
            self._metrics[metric.name] = metric
        self._save()

    def update_metric(self, metric: Metric) -> None:
        """
        Update an existing metric.

        Args:
            metric (Metric): The metric to update
        """
        if metric.name not in self._metrics:
            raise KeyError(
                f"Metric with name '{metric.name}' does not exist in project"
            )
        self._metrics[metric.name] = metric
        self._save()

    def get_metric(self, metric_name: str) -> Metric:
        """
        Get a metric by name.

        Args:
            metric_name (str): The name of the metric to get

        Returns:
            Metric: The metric
        """
        if metric_name not in self._metrics:
            raise KeyError(
                f"Metric with name '{metric_name}' does not exist in project"
            )
        return self._metrics[metric_name]

    def get_metrics_by_names(self, metric_names: List[str]) -> List[Metric]:
        """
        Get multiple metrics by their names.

        Args:
            metric_names (List[str]): The names of the metrics to get

        Returns:
            List[Metric]: The metrics
        """
        missing = [name for name in metric_names if name not in self._metrics]
        if missing:
            raise KeyError(f"Metrics not found in project: {', '.join(missing)}")
        return [self._metrics[name] for name in metric_names]

    def remove_metric(self, metric_name: str) -> None:
        """
        Remove a metric by name.

        Args:
            metric_name (str): The name of the metric to remove
        """
        if metric_name not in self._metrics:
            raise KeyError(
                f"Metric with name '{metric_name}' does not exist in project"
            )
        del self._metrics[metric_name]
        self._save()

    def list_metric_names(self) -> List[str]:
        """Get all metric names."""
        return list(self._metrics.keys())

    # Success Criteria Methods
    @property
    def success_criteria(self):
        """Get the success criteria of the project"""
        return self._success_criteria

    def update_success_criteria(self, success_criteria: Optional[str]) -> None:
        """Update the success criteria of the project

        Args:
            success_criteria (Optional[str]): The new success criteria. If it is None, the success criteria will be removed
        """
        self._success_criteria = success_criteria
        self._save()

    # Version methods
    @property
    def version_ids(self):
        """Get all version names in the project"""
        all_files = os.listdir(os.path.join(self._project_folder, "versions"))
        return [
            f
            for f in all_files
            if os.path.isdir(os.path.join(self._project_folder, "versions", f))
        ]

    def create_version(
        self,
        version_id: str,
        prompt: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Create a new version in the project

        Args:
            version_id (str): Name of the version
            prompt (str): Prompt used by the voice agent
            metadata (Optional[Dict[str, Any]]): Metadata to be associated with the version. Defaults to None.
        """  # noqa E501
        validate_name(version_id, "version_id")
        if version_id in self.version_ids:
            raise FileExistsError(f"Version {version_id} already exists")
        version_folder = os.path.join(self._project_folder, "versions", version_id)
        os.makedirs(version_folder)
        os.makedirs(os.path.join(version_folder, "recordings"))
        os.makedirs(os.path.join(version_folder, "steps"))
        version = Version(version_id, self.id, prompt, metadata)
        version._save()
        return version

    def load_version(self, version_id: str) -> Version:
        """Load a version from the project

        Args:
            version_id (str): ID of the version to load
        """
        if version_id not in self.version_ids:
            raise KeyError(f"Version {version_id} does not exist")
        return Version._load(self.id, version_id)

    # Evaluator methods
    def create_evaluator(
        self, test_cases: List[str], metric_names: Optional[List[str]] = None
    ) -> Evaluator:
        """
        Create a new evaluator for the project

        Args:
            test_cases (List[str]): List of test cases to evaluate the agent on.
            metrics (Optional[List[str]]): List of metric names to be evaluated, or None to use all project metrics.

        Returns:
            Evaluator: The newly created evaluator
        """  # noqa E501
        if self.list_metric_names() == []:
            raise ValueError(
                "No metrics found in project. Add metrics during project creation or using add_metrics() before creating an evaluator."
            )
        if metric_names is not None:
            self.get_metrics_by_names(metric_names)  # check for existence
        else:
            metric_names = self.list_metric_names()

        if not metric_names:
            raise ValueError("No metrics provided.")
        if not test_cases:
            raise ValueError("No test cases provided.")

        eval_id = uuid4().hex
        cur_eval = Evaluator(
            eval_id,
            self.id,
            metric_names,
            test_cases,
        )

        self._evals[eval_id] = cur_eval
        self._save()
        return cur_eval

    def load_evaluator(self, eval_id: str) -> Evaluator:
        """
        Load an evaluator from the project

        Args:
            eval_id (str): ID of the evaluator to load

        Returns:
            Evaluator: The loaded evaluator
        """
        if eval_id not in self._evals:
            raise KeyError(f"Evaluator {eval_id} does not exist")
        return self._evals[eval_id]

    def list_evaluators(self) -> List[Evaluator]:
        """Get all evaluators in the project"""
        return list(self._evals.values())

    # Internal Use Methods
    @property
    def _project_folder(self) -> str:
        return os.path.join(constants.PROJECTS_FOLDER, self.id)

    @property
    def _path(self) -> str:
        return get_info_path(self.id)

    def _get_paths(self) -> List[str]:
        paths = []
        for version_id in self.version_ids:
            version = self.load_version(version_id)
            paths.extend(version._get_paths())
        return paths

    def _get_step_names(self) -> List[str]:
        step_names = set()
        for version_id in self.version_ids:
            version = self.load_version(version_id)
            step_names.union(version._get_step_names())
        return list(step_names)

    def _save(self):
        metrics = {k: v.to_dict() for k, v in self._metrics.items()}
        d = {
            "success_criteria": self._success_criteria,
            "eval_ids": list(self._evals.keys()),
            "metrics": metrics,
        }
        save_json(d, self._path)

    @classmethod
    def _load(cls, project_id):
        try:
            load_path = get_info_path(project_id)
            d = load_json(load_path)
            metrics = d.pop("metrics")
            metrics = {
                k: Metric(
                    name=k,
                    definition=v["definition"],
                    scoring=v["scoring"],
                    include_prompt=v["include_prompt"],
                )
                for k, v in metrics.items()
            }
            eval_ids = d.pop("eval_ids")
            evals = {
                eval_id: Evaluator._load(project_id, eval_id) for eval_id in eval_ids
            }
            success_criteria = d.get("success_criteria", None)
            evals = {k: v for k, v in evals.items() if v}
            return cls(
                project_id,
                success_criteria=success_criteria,
                evals=evals,
                _metrics=metrics,
            )
        except FileNotFoundError:
            return cls(project_id)
