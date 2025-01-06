import os
import time
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Type
from uuid import uuid4

import mixedvoices as mv
import mixedvoices.constants as constants
from mixedvoices.evaluation.eval_run import EvalRun
from mixedvoices.utils import load_json, save_json

if TYPE_CHECKING:
    from mixedvoices import BaseAgent  # pragma: no cover
    from mixedvoices.core.version import Version  # pragma: no cover


def get_info_path(project_id: str, eval_id: str):
    return os.path.join(
        constants.PROJECTS_FOLDER,
        project_id,
        "evals",
        eval_id,
        "info.json",
    )


class Evaluator:
    """Evaluator is a reusable collections of tests cases and metrics to test model performance.
    These can be run multiple times across different versions to track performance.
    """

    def __init__(
        self,
        eval_id: str,
        project_id: str,
        metric_names: List[str],
        test_cases: List[str],
        created_at: Optional[int] = None,
        eval_runs: Optional[dict[str, EvalRun]] = None,
    ):
        self._eval_id = eval_id
        self._project_id = project_id
        self._metric_names = metric_names
        self._test_cases = test_cases
        self._created_at = created_at or int(time.time())
        self._eval_runs = eval_runs or {}
        self._cached_project = None
        self._save()

    @property
    def id(self) -> str:
        """Get the id of the Evaluator"""
        return self._eval_id

    @property
    def project_id(self) -> str:
        """Get the name of the Project"""
        return self._project_id

    @property
    def metric_names(self) -> List[str]:
        """List of metric names to be evaluated"""
        return self._metric_names

    @property
    def test_cases(self) -> List[str]:
        """List of test cases to be evaluated"""
        return self._test_cases

    @property
    def info(self) -> Dict[str, Any]:
        """Get the info of the evaluator as a dictionary"""
        return {
            "eval_id": self.id,
            "created_at": self._created_at,
            "num_prompts": len(self.test_cases),
            "num_eval_runs": len(self.list_eval_runs()),
            "metric_names": self.metric_names,
        }

    def list_eval_runs(self, version_id: Optional[str] = None) -> List[EvalRun]:
        """List of eval runs"""
        if version_id and version_id not in self._project.version_ids:
            raise KeyError(
                f"Version {version_id} not found in project {self.project_id}"
            )
        all_runs = list(self._eval_runs.values())
        if version_id:
            all_runs = [run for run in all_runs if run.version_id == version_id]
        return all_runs

    def load_eval_run(self, run_id: str) -> EvalRun:
        """Load an eval run from id

        Args:
            run_id (str): The id of the eval run
        """
        if run_id not in self._eval_runs:
            raise KeyError(f"Eval run {run_id} not found")
        return self._eval_runs[run_id]

    def run(
        self,
        version: "Version",
        agent_class: Type["BaseAgent"],
        agent_starts: Optional[bool],
        verbose: bool = True,
        **kwargs,
    ) -> EvalRun:
        """Runs the evaluator and saves the results.

        Args:
            version (Version): The version of the project to evaluate
            agent_class (Type[BaseAgent]): The agent class to evaluate
            agent_starts (Optional[bool]): Whether the agent starts the conversation or not.
                If True, the agent starts the conversation
                If False, the evaluator starts the conversation
                If None, random choice
            verbose (bool): Whether to print testing conversation and scores. Defaults to True
            **kwargs: Keyword arguments to pass to the agent class
        """

        run_id = uuid4().hex
        project = self._project
        version_id = version.id
        if version_id not in project.version_ids:
            raise ValueError("Evaluator can only be run on a version of the project")
        prompt = version._prompt
        run = EvalRun(
            run_id,
            self.project_id,
            version_id,
            self.id,
            prompt,
            self._metric_names,
            self._test_cases,
            verbose,
        )
        self._eval_runs[run_id] = run
        self._save()
        run.run(agent_class, agent_starts, **kwargs)
        return run

    @property
    def _project(self):
        if self._cached_project is None:
            self._cached_project = mv.load_project(self.project_id)
        return self._cached_project

    @property
    def _path(self):
        return get_info_path(self.project_id, self.id)

    def _save(self):
        os.makedirs(os.path.dirname(self._path), exist_ok=True)
        d = {
            "metric_names": self._metric_names,
            "test_cases": self._test_cases,
            "created_at": self._created_at,
            "eval_run_ids": list(self._eval_runs.keys()),
            "eval_run_version_ids": [
                run.version_id for run in self._eval_runs.values()
            ],
        }
        save_json(d, self._path)

    @classmethod
    def _load(cls, project_id, eval_id):
        load_path = get_info_path(project_id, eval_id)
        try:
            d = load_json(load_path)
        except FileNotFoundError:
            return

        eval_run_ids = d.pop("eval_run_ids")
        eval_run_version_ids = d.pop("eval_run_version_ids")
        eval_runs = {
            run_id: EvalRun._load(project_id, version_id, eval_id, run_id)
            for run_id, version_id in zip(eval_run_ids, eval_run_version_ids)
        }
        d.update(
            {
                "project_id": project_id,
                "eval_id": eval_id,
                "eval_runs": eval_runs,
            }
        )

        return cls(**d)
