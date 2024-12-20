import json
import os
from datetime import datetime

from openai import OpenAI

import mixedvoices.constants as constants
from mixedvoices.evaluation.utils import history_to_transcript
from mixedvoices.processors.llm_metrics import get_llm_metrics

client = OpenAI()

model = "gpt-4o"


class EvalAgent:
    def __init__(
        self,
        agent_id,
        project_id,
        version_id,
        run_id,
        prompt,
        eval_prompt,
        enabled_llm_metrics,
        history=None,
        end=None,
        transcript=None,
        scores=None,
        error=None,
    ):
        self.agent_id = agent_id
        self.project_id = project_id
        self.version_id = version_id
        self.run_id = run_id
        self.prompt = prompt
        self.eval_prompt = eval_prompt
        self.enabled_llm_metrics = enabled_llm_metrics
        self.history = history or []
        self.end = end or False
        self.transcript = transcript or None
        self.scores = scores or None
        self.error = error or None

    def respond(self, input, end=False):
        if input:
            self.history.append({"role": "user", "content": input})
        if end:
            self.handle_conversation_end()
            return
        messages = [self.get_system_prompt()] + self.history
        try:
            response = client.chat.completions.create(model=model, messages=messages)
            assistant_response = response.choices[0].message.content
            self.history.append({"role": "assistant", "content": assistant_response})
            return assistant_response
        except Exception as e:
            self.handle_exception(e)

    def handle_conversation_end(self):
        self.end = True
        self.transcript = history_to_transcript(self.history)
        self.scores = get_llm_metrics(
            self.transcript, self.prompt, **self.enabled_llm_metrics
        )
        self.save()

    def handle_exception(self, e):
        self.error = str(e)
        self.end = True
        self.transcript = history_to_transcript(self.history)
        self.save()

    def get_system_prompt(self):
        return {
            "role": "system",
            "content": f"{self.eval_prompt}\nCurrent date and time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}. You will start by greeting. Keep your response short, under 20 words.",  # TODO: this is local time on server
        }

    @property
    def path(self):
        return os.path.join(
            constants.ALL_PROJECTS_FOLDER,
            self.project_id,
            self.version_id,
            "eval_runs",
            self.run_id,
            "agents",
            self.agent_id,
        )

    def save(self):
        os.makedirs(self.path, exist_ok=True)
        save_path = os.path.join(self.path, "info.json")
        with open(save_path, "w") as f:
            d = {
                "prompt": self.prompt,
                "eval_prompt": self.eval_prompt,
                "enabled_llm_metrics": self.enabled_llm_metrics,
                "history": self.history,
                "end": self.end,
                "transcript": self.transcript,
                "scores": self.scores,
                "error": self.error,
            }
            f.write(json.dumps(d))

    @classmethod
    def load(cls, project_id, version_id, run_id, agent_id):
        load_path = os.path.join(
            constants.ALL_PROJECTS_FOLDER,
            project_id,
            version_id,
            "eval_runs",
            run_id,
            "agents",
            agent_id,
            "info.json",
        )
        with open(load_path, "r") as f:
            d = json.loads(f.read())

        d.update(
            {
                "project_id": project_id,
                "version_id": version_id,
                "run_id": run_id,
                "agent_id": agent_id,
            }
        )
        return cls(**d)
