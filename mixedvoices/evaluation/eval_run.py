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


class EvalRun:
    def __init__(
        self,
        run_id: str,
        project_id: str,
        version_id: str,
        eval_id: str,
        prompt: str,
        metric_names: List[str],
        eval_prompts: List[str],
        created_at: Optional[int] = None,
        eval_agents: Optional[List[EvalAgent]] = None,
    ):
        self.run_id = run_id
        self.project_id = project_id
        self.version_id = version_id
        self.eval_id = eval_id

        self.prompt = prompt
        self.metric_names = metric_names
        self.eval_prompts = eval_prompts
        self.created_at = created_at or int(time.time())
        self.eval_agents = eval_agents or [
            EvalAgent(
                uuid4().hex,
                project_id,
                version_id,
                eval_id,
                run_id,
                prompt,
                eval_prompt,
                metric_names,
            )
            for eval_prompt in self.eval_prompts
        ]
        self.save()

    @property
    def path(self):
        return get_info_path(
            self.project_id, self.version_id, self.eval_id, self.run_id
        )

    def save(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        d = {
            "prompt": self.prompt,
            "metric_names": self.metric_names,
            "eval_prompts": self.eval_prompts,
            "created_at": self.created_at,
            "eval_agent_ids": [a.agent_id for a in self.eval_agents],
        }
        save_json(d, self.path)

    @classmethod
    def load(cls, project_id, version_id, eval_id, run_id):
        load_path = get_info_path(project_id, version_id, eval_id, run_id)
        try:
            d = load_json(load_path)
        except FileNotFoundError:
            return

        eval_agent_ids = d.pop("eval_agent_ids")
        eval_agents = [
            EvalAgent.load(project_id, version_id, eval_id, run_id, agent_id)
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

    def __iter__(self):
        yield from self.eval_agents

    def run(
        self, agent_class: Type["BaseAgent"], agent_starts: Optional[bool], **kwargs
    ):
        """Runs the evaluator and saves the results.

        Args:
            agent_class: The agent class to evaluate.
            agent_starts: Whether the agent starts the conversation or not.
                If True, the agent starts the conversation
                If False, the evaluator starts the conversation
                If None, random choice
            **kwargs: Keyword arguments to pass to the agent class
        """
        for eval_agent in self.eval_agents:
            eval_agent.evaluate(agent_class, agent_starts, **kwargs)
            self.save()
