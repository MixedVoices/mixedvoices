import os
import time
from typing import TYPE_CHECKING, List, Optional, Type
from uuid import uuid4

import mixedvoices as mv
import mixedvoices.constants as constants
from mixedvoices.evaluation.eval_run import EvalRun
from mixedvoices.metrics import deserialize_metrics, serialize_metrics
from mixedvoices.utils import load_json, save_json

if TYPE_CHECKING:
    from mixedvoices import BaseAgent  # pragma: no cover
    from mixedvoices.core.version import Version  # pragma: no cover
    from mixedvoices.metrics import Metric  # pragma: no cover


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
        metrics: List["Metric"],
        eval_prompts: List[str],
        created_at: Optional[int] = None,
        eval_runs: Optional[List[EvalRun]] = None,
    ):
        self.eval_id = eval_id
        self.project_id = project_id
        self.metrics = metrics
        self.eval_prompts = eval_prompts
        self.created_at = created_at or int(time.time())
        self.eval_runs = eval_runs or []
        self.save()

    @property
    def path(self):
        return get_info_path(self.project_id, self.eval_id)

    def save(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        d = {
            "metrics": serialize_metrics(self.metrics),
            "eval_prompts": self.eval_prompts,
            "created_at": self.created_at,
            "eval_run_ids": [a.run_id for a in self.eval_runs],
        }
        save_json(d, self.path)

    @classmethod
    def load(cls, project_id, eval_id):
        load_path = get_info_path(project_id, eval_id)
        try:
            d = load_json(load_path)
        except FileNotFoundError:
            return
        eval_run_ids = d.pop("eval_run_ids")
        eval_runs = [
            EvalRun.load(project_id, eval_id, run_id) for run_id in eval_run_ids
        ]

        metrics = deserialize_metrics(d.pop("metrics"))
        d.update(
            {
                "project_id": project_id,
                "eval_id": eval_id,
                "eval_runs": eval_runs,
                "metrics": metrics,
            }
        )

        return cls(**d)

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
        if version_id not in project.versions:
            raise ValueError("Evaluator can only be run on a version of the project")
        prompt = version.prompt
        run = EvalRun(
            run_id,
            self.project_id,
            version_id,
            self.eval_id,
            prompt,
            self.metrics,
            self.eval_prompts,
        )
        self.eval_runs.append(run)
        self.save()
        run.run(agent_class, agent_starts, **kwargs)
