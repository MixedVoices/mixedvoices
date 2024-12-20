import json
import os
import time
from typing import List, Optional
from uuid import uuid4

import mixedvoices.constants as constants
from mixedvoices.evaluation.eval_agent import EvalAgent


class EvaluationRun:
    def __init__(
        self,
        run_id: str,
        project_id: str,
        version_id: str,
        prompt: str,
        enabled_llm_metrics: dict,
        eval_prompts: List[str],
        created_at: Optional[int] = None,
        eval_agents: Optional[List[EvalAgent]] = None,
    ):
        self.run_id = run_id
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
                run_id,
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
            "eval_runs",
            self.run_id,
        )

    def save(self):
        for agent in self.eval_agents:
            agent.save()
        os.makedirs(self.path, exist_ok=True)
        save_path = os.path.join(self.path, "info.json")
        with open(save_path, "w") as f:
            d = {
                "prompt": self.prompt,
                "enabled_llm_metrics": self.enabled_llm_metrics,
                "eval_prompts": self.eval_prompts,
                "created_at": self.created_at,
                "eval_agent_ids": [a.agent_id for a in self.eval_agents],
            }
            f.write(json.dumps(d))

    @classmethod
    def load(cls, project_id, version_id, run_id):
        load_path = os.path.join(
            constants.ALL_PROJECTS_FOLDER,
            project_id,
            version_id,
            "eval_runs",
            run_id,
            "info.json",
        )
        with open(load_path, "r") as f:
            d = json.loads(f.read())

        eval_agent_ids = d.pop("eval_agent_ids")
        eval_agents = [
            EvalAgent.load(project_id, version_id, run_id, agent_id)
            for agent_id in eval_agent_ids
        ]
        d.update(
            {
                "project_id": project_id,
                "version_id": version_id,
                "run_id": run_id,
                "eval_agents": eval_agents,
            }
        )

        return cls(**d)

    def __iter__(self):
        yield from self.eval_agents
