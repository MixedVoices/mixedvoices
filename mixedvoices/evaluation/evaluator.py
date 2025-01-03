import os
import time
from typing import TYPE_CHECKING, List, Optional, Type
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
    def __init__(
        self,
        eval_id: str,
        project_id: str,
        metric_names: List[str],
        test_cases: List[str],
        created_at: Optional[int] = None,
        eval_runs: Optional[dict[str, EvalRun]] = None,
    ):
        self.eval_id = eval_id
        self.project_id = project_id
        self._metric_names = metric_names
        self._test_cases = test_cases
        self._created_at = created_at or int(time.time())
        self._eval_runs = eval_runs or {}
        self._save()

    @property
    def metric_names(self) -> List[str]:
        """List of metric names to be evaluated"""
        return self._metric_names

    @property
    def test_cases(self) -> List[str]:
        """List of test cases to be evaluated"""
        return self._test_cases

    # TODO: Expose eval runs as property for users to extract info from

    def run(
        self,
        version: "Version",
        agent_class: Type["BaseAgent"],
        agent_starts: Optional[bool],
        **kwargs,
    ):
        """Runs the evaluator and saves the results.

        Args:
            version: The version of the project to evaluate
            agent_class: The agent class to evaluate.
            agent_starts: Whether the agent starts the conversation or not.
                If True, the agent starts the conversation
                If False, the evaluator starts the conversation
                If None, random choice
            **kwargs: Keyword arguments to pass to the agent class
        """

        run_id = uuid4().hex
        project = mv.load_project(self.project_id)
        version_id = version.version_id
        if version_id not in project.version_names:
            raise ValueError("Evaluator can only be run on a version of the project")
        prompt = version._prompt
        run = EvalRun(
            run_id,
            self.project_id,
            version_id,
            self.eval_id,
            prompt,
            self._metric_names,
            self._test_cases,
        )
        self._eval_runs[run_id] = run
        self._save()
        run.run(agent_class, agent_starts, **kwargs)

    @property
    def _path(self):
        return get_info_path(self.project_id, self.eval_id)

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
            run_id: EvalRun.load(project_id, version_id, eval_id, run_id)
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
