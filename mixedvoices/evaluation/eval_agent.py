import json
import os
import random
from datetime import datetime
from typing import TYPE_CHECKING, Type

from openai import OpenAI

import mixedvoices.constants as constants
from mixedvoices.evaluation.utils import history_to_transcript
from mixedvoices.processors.llm_metrics import get_llm_metrics

if TYPE_CHECKING:
    from mixedvoices import BaseAgent

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
        started=False,
        ended=False,
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
        self.started = started
        self.ended = ended
        self.transcript = transcript or None
        self.scores = scores or None
        self.error = error or None

    def respond(self, input):
        if not self.started:
            self.started = True
            self.save()
        if input:
            self.history.append({"role": "user", "content": input})
        messages = [self.get_system_prompt()] + self.history
        try:
            response = client.chat.completions.create(model=model, messages=messages)
            assistant_response = response.choices[0].message.content
            self.history.append({"role": "assistant", "content": assistant_response})
            return assistant_response
        except Exception as e:
            self.handle_exception(e, "Conversation")

    def handle_conversation_end(self):
        self.ended = True
        self.transcript = history_to_transcript(self.history)
        try:
            self.scores = get_llm_metrics(
                self.transcript, self.prompt, **self.enabled_llm_metrics
            )
            print(self.scores)
            self.save()
        except Exception as e:
            self.handle_exception(e, "Metric Calculation")

    def handle_exception(self, e, source):
        self.error = f"Error Source: {source} \nError: {str(e)}"
        self.ended = True
        self.transcript = self.transcript or history_to_transcript(self.history)
        self.save()

    def get_system_prompt(self):
        return {
            "role": "system",
            "content": f"{self.eval_prompt}"
            f"\nDate/time: {datetime.now().strftime('%I%p, %a, %d %b').lower().lstrip('0')}."
            "\nKeep responses short, under 20 words.",
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
                "started": self.started,
                "ended": self.ended,
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
        try:
            with open(load_path, "r") as f:
                d = json.loads(f.read())
        except FileNotFoundError:
            return

        d.update(
            {
                "project_id": project_id,
                "version_id": version_id,
                "run_id": run_id,
                "agent_id": agent_id,
            }
        )
        return cls(**d)

    def evaluate(self, agent_class: Type["BaseAgent"]):
        assistant = agent_class()

        assistant_starts = assistant.starts_conversation

        if assistant_starts is None:
            assistant_starts = random.choice([True, False])

        assistant_message = assistant.respond("") if assistant_starts else ""
        # TODO: Add case when evaluator ends conversation
        while 1:
            if assistant.conversation_ended:
                self.handle_conversation_end()
                break
            evaluator_message = self.respond(assistant_message)
            assistant_message = assistant.respond(evaluator_message)
            print(f"Evaluator: {evaluator_message}")
            print(f"Assistant: {assistant_message}\n")
