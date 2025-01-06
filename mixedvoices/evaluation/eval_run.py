import os
import time
from typing import TYPE_CHECKING, List, Optional, Type
from uuid import uuid4

import mixedvoices.constants as constants
from mixedvoices.evaluation.eval_agent import EvalAgent
from mixedvoices.utils import load_json, save_json

if TYPE_CHECKING:
    from mixedvoices import BaseAgent  # pragma: no cover


def get_info_path(project_id, version_id, eval_id, run_id):
    return os.path.join(
        constants.PROJECTS_FOLDER,
        project_id,
        "evals",
        eval_id,
        "versions",
        version_id,
        "runs",
        run_id,
        "info.json",
    )


# TODO add resume later


class EvalRun:
    """Tracks a single run of Evaluator"""
    def __init__(
        self,
        run_id: str,
        project_id: str,
        version_id: str,
        eval_id: str,
        agent_prompt: str,
        metric_names: List[str],
        test_cases: List[str],
        verbose: bool = True,
        created_at: Optional[int] = None,
        eval_agents: Optional[List[EvalAgent]] = None,
        started: bool = False,
        ended: bool = False,
        error: Optional[str] = None,
        last_updated: Optional[int] = None,
    ):
        self._run_id = run_id
        self._project_id = project_id
        self._version_id = version_id
        self._eval_id = eval_id

        self._agent_prompt = agent_prompt
        self._metric_names = metric_names
        self._test_cases = test_cases
        self._verbose = verbose
        self._created_at = created_at or int(time.time())
        self._eval_agents = eval_agents or [
            EvalAgent(
                uuid4().hex,
                project_id,
                version_id,
                eval_id,
                run_id,
                agent_prompt,
                test_case,
                metric_names,
                verbose,
            )
            for test_case in self._test_cases
        ]
        self._started = started
        self._ended = ended
        self._error = error
        self._last_updated = last_updated
        self._save()

    @property
    def id(self) -> str:
        """Get the id of the EvalRun"""
        return self._run_id

    @property
    def project_id(self) -> str:
        """Get the name of the Project"""
        return self._project_id

    @property
    def version_id(self) -> str:
        """Get the name of the Version"""
        return self._version_id

    @property
    def eval_id(self) -> str:
        """Get the id of the Evaluator"""
        return self._eval_id

    def run(
        self,
        agent_class: Type["BaseAgent"],
        agent_starts: Optional[bool],
        **kwargs,
    ):
        """Runs the evaluator and saves the results.

        Args:
            agent_class (Type[BaseAgent]): The agent class to evaluate
            agent_starts (Optional[bool]): Whether the agent starts the conversation or not.
                If True, the agent starts the conversation
                If False, the evaluator starts the conversation
                If None, random choice
            **kwargs: Keyword arguments to pass to the agent class
        """
        if self._started:
            raise ValueError(
                "This run was already started. Create a new run to test again."
            )

        if self._verbose:
            print(f"Starting Evaluation of {len(self._test_cases)} Test Cases")
        self._started = True
        for i, eval_agent in enumerate(self._eval_agents):
            try:
                eval_agent.evaluate(agent_class, agent_starts, i + 1, **kwargs)
            except Exception as e:
                self._error = f"Error Source: EvalRun Run \nError: {str(e)}"
                self._save()
                raise RuntimeError(f"Error evaluating agent: {str(e)}") from e
            self._save()
        self._ended = True

    @property
    def status(self):
        """Returns the status of the run as a string"""
        if self._error:
            return "FAILED"
        if not self._started:
            return "PENDING"
        if self._ended:
            return "COMPLETED"
        current_time = int(time.time())
        if current_time - self._last_updated < 300:
            return "IN PROGRESS"
        return "INTERRUPTED"

    @property
    def results(self) -> List[dict]:
        """Returns the results of the run as a list of dictionaries each representing a test case's results"""
        return [agent.results() for agent in self._eval_agents]

    @property
    def info(self):
        """Get the info of the run as a dictionary"""
        return {
            "project_id": self.project_id,
            "version_id": self.version_id,
            "eval_id": self.eval_id,
            "run_id": self.id,
            "created_at": self._created_at,
        }

    @property
    def _path(self):
        return get_info_path(self.project_id, self.version_id, self.eval_id, self.id)

    def _save(self):
        self._last_updated = int(time.time())
        os.makedirs(os.path.dirname(self._path), exist_ok=True)
        d = {
            "agent_prompt": self._agent_prompt,
            "metric_names": self._metric_names,
            "test_cases": self._test_cases,
            "created_at": self._created_at,
            "eval_agent_ids": [a.id for a in self._eval_agents],
            "started": self._started,
            "ended": self._ended,
        }
        save_json(d, self._path)

    @classmethod
    def _load(cls, project_id, version_id, eval_id, run_id):
        load_path = get_info_path(project_id, version_id, eval_id, run_id)
        try:
            d = load_json(load_path)
        except FileNotFoundError:
            return

        eval_agent_ids = d.pop("eval_agent_ids")
        eval_agents = [
            EvalAgent._load(project_id, version_id, eval_id, run_id, agent_id)
            for agent_id in eval_agent_ids
        ]
        eval_agents = [a for a in eval_agents if a]

        d.update(
            {
                "project_id": project_id,
                "version_id": version_id,
                "eval_id": eval_id,
                "run_id": run_id,
                "eval_agents": eval_agents,
            }
        )

        return cls(**d)
