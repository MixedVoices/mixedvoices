import os
import random
from datetime import datetime
from typing import TYPE_CHECKING, Type

import mixedvoices.constants as constants
from mixedvoices.evaluation.utils import history_to_transcript
from mixedvoices.processors.llm_metrics import get_llm_metrics
from mixedvoices.utils import get_openai_client, load_json, save_json

if TYPE_CHECKING:
    from mixedvoices import BaseAgent

model = "gpt-4o"


def has_ended_conversation(message):
    return "HANGUP" in message


# TODO: Better logging and better model management throughout
class EvalAgent:
    def __init__(
        self,
        agent_id,
        project_id,
        version_id,
        eval_id,
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
        self.eval_id = eval_id
        self.prompt = prompt
        self.eval_prompt = eval_prompt
        self.enabled_llm_metrics = enabled_llm_metrics
        self.history = history or []
        self.started = started
        self.ended = ended
        self.transcript = transcript or None
        self.scores = scores or None
        self.error = error or None
        self.save()

    def respond(self, input):
        if not self.started:
            self.started = True
            self.save()
        if input:
            self.add_user_message(input)
        messages = [self.get_system_prompt()] + self.history
        try:
            client = get_openai_client()
            response = client.chat.completions.create(model=model, messages=messages)
            assistant_response = response.choices[0].message.content
            self.add_assistant_message(assistant_response)
            return assistant_response, has_ended_conversation(assistant_response)
        except Exception as e:
            self.handle_exception(e, "Conversation")

    def add_user_message(self, message):
        self.history.append({"role": "user", "content": message})
        print(f"Assistant: {message}")  # Here user is REAL agent

    def add_assistant_message(self, message):
        self.history.append({"role": "assistant", "content": message})
        print(f"Evaluator: {message}")  # Here assistant is EVAL agent

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
            "content": f"You are a testing agent. Have a conversation, don't make sounds."
            f"\n{self.eval_prompt}"
            "\nWhen conversation is complete, along with final response, return HANGUP to end."
            "\nEg: Have a good day. HANGUP"
            f"\nDate/time: {datetime.now().strftime('%I%p, %a, %d %b').lower().lstrip('0')}."
            "\nKeep responses short, under 20 words.",
        }

    @property
    def path(self):
        return os.path.join(
            constants.ALL_PROJECTS_FOLDER,
            self.project_id,
            self.version_id,
            "evals",
            self.eval_id,
            "agents",
            self.agent_id,
        )

    def save(self):
        os.makedirs(self.path, exist_ok=True)
        save_path = os.path.join(self.path, "info.json")
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
        save_json(d, save_path)

    @classmethod
    def load(cls, project_id, version_id, eval_id, agent_id):
        load_path = os.path.join(
            constants.ALL_PROJECTS_FOLDER,
            project_id,
            version_id,
            "evals",
            eval_id,
            "agents",
            agent_id,
            "info.json",
        )
        try:
            d = load_json(load_path)
        except FileNotFoundError:
            return

        d.update(
            {
                "project_id": project_id,
                "version_id": version_id,
                "eval_id": eval_id,
                "agent_id": agent_id,
            }
        )
        return cls(**d)

    def evaluate(self, agent_class: Type["BaseAgent"]):
        assistant = agent_class()
        assistant_starts = assistant.starts_conversation
        if assistant_starts is None:
            assistant_starts = random.choice([True, False])

        if assistant_starts:
            assistant_message, ended = assistant.respond("")
        else:
            assistant_message, ended = "", False
        while 1:
            evaluator_message, ended = self.respond(assistant_message)
            if ended:
                break
            assistant_message, ended = assistant.respond(evaluator_message)
            if ended:
                self.add_user_message(assistant_message)
                break

        self.handle_conversation_end()
