import os
import time
from typing import TYPE_CHECKING, List, Optional, Type
from uuid import uuid4

import mixedvoices.constants as constants
from mixedvoices.evaluation.eval_agent import EvalAgent
from mixedvoices.utils import load_json, save_json

if TYPE_CHECKING:
    from mixedvoices import BaseAgent


class Evaluator:
    def __init__(
        self,
        eval_id: str,
        project_id: str,
        version_id: str,
        prompt: str,
        enabled_llm_metrics: dict,
        eval_prompts: List[str],
        created_at: Optional[int] = None,
        eval_agents: Optional[List[EvalAgent]] = None,
    ):
        self.eval_id = eval_id
        self.project_id = project_id
        self.version_id = version_id
        self.prompt = prompt
        self.enabled_llm_metrics = enabled_llm_metrics
        self.eval_prompts = eval_prompts
        self.created_at = created_at or int(time.time())
        self.eval_agents = eval_agents or [
            EvalAgent(
                uuid4().hex,
                project_id,
                version_id,
                eval_id,
                prompt,
                eval_prompt,
                enabled_llm_metrics,
            )
            for eval_prompt in self.eval_prompts
        ]
        self.save()

    @property
    def path(self):
        return os.path.join(
            constants.ALL_PROJECTS_FOLDER,
            self.project_id,
            self.version_id,
            "evals",
            self.eval_id,
        )

    def save(self):
        os.makedirs(self.path, exist_ok=True)
        save_path = os.path.join(self.path, "info.json")
        d = {
            "prompt": self.prompt,
            "enabled_llm_metrics": self.enabled_llm_metrics,
            "eval_prompts": self.eval_prompts,
            "created_at": self.created_at,
            "eval_agent_ids": [a.agent_id for a in self.eval_agents],
        }
        save_json(d, save_path)

    @classmethod
    def load(cls, project_id, version_id, eval_id):
        load_path = os.path.join(
            constants.ALL_PROJECTS_FOLDER,
            project_id,
            version_id,
            "evals",
            eval_id,
            "info.json",
        )
        try:
            d = load_json(load_path)
        except FileNotFoundError:
            return

        eval_agent_ids = d.pop("eval_agent_ids")
        eval_agents = [
            EvalAgent.load(project_id, version_id, eval_id, agent_id)
            for agent_id in eval_agent_ids
        ]
        eval_agents = [a for a in eval_agents if a]
        d.update(
            {
                "project_id": project_id,
                "version_id": version_id,
                "eval_id": eval_id,
                "eval_agents": eval_agents,
            }
        )

        return cls(**d)

    def __iter__(self):
        yield from self.eval_agents

    def run(self, agent_class: Type["BaseAgent"]):
        for eval_agent in self.eval_agents:
            eval_agent.evaluate(agent_class)
            self.save()
