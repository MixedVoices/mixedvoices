import os
import random
from datetime import datetime
from typing import TYPE_CHECKING, List, Type

import mixedvoices as mv
import mixedvoices.constants as constants
from mixedvoices.evaluation.utils import history_to_transcript
from mixedvoices.metrics.metric import Metric
from mixedvoices.processors.llm_metrics import generate_scores
from mixedvoices.utils import get_openai_client, load_json, save_json

if TYPE_CHECKING:
    from mixedvoices import BaseAgent  # pragma: no cover

model = "gpt-4o"


def has_ended_conversation(message):
    return "HANGUP" in message


def get_info_path(project_id, version_id, eval_id, run_id, agent_id):
    return os.path.join(
        constants.PROJECTS_FOLDER,
        project_id,
        "evals",
        eval_id,
        "versions",
        version_id,
        "runs",
        run_id,
        "agents",
        agent_id,
        "info.json",
    )


# TODO: Better logging and better model management throughout
class EvalAgent:
    def __init__(
        self,
        agent_id,
        project_id,
        version_id,
        eval_id,
        run_id,
        prompt,
        eval_prompt,
        metric_names,
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
        self.run_id = run_id

        self.prompt = prompt
        self.eval_prompt = eval_prompt
        self.metric_names = metric_names
        self.history = history or []
        self.started = started
        self.ended = ended
        self.transcript = transcript or None
        self.scores = scores or None
        self.error = error or None
        self.save()

    @property
    def metrics(self) -> List[Metric]:
        project = mv.load_project(self.project_id)
        return project.get_metrics_by_names(self.metric_names)

    def respond(self, input):
        if not self.started:
            self.started = True
            self.save()
        if input:
            self.add_agent_message(input)
        messages = [self.get_system_prompt()] + self.history
        try:
            client = get_openai_client()
            response = client.chat.completions.create(model=model, messages=messages)
            evaluator_response = response.choices[0].message.content
            self.add_eval_agent_message(evaluator_response)
            return evaluator_response, has_ended_conversation(evaluator_response)
        except Exception as e:
            self.handle_exception(e, "Conversation")

    def add_agent_message(self, message):
        self.history.append({"role": "user", "content": message})
        print(f"Agent: {message}")

    def add_eval_agent_message(self, message):
        self.history.append({"role": "assistant", "content": message})
        print(f"Evaluator: {message}")

    def handle_conversation_end(self):
        self.ended = True
        self.transcript = history_to_transcript(self.history)
        try:
            self.scores = generate_scores(self.transcript, self.prompt, self.metrics)
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
        datetime_str = datetime.now().strftime("%I%p, %a, %d %b").lower().lstrip("0")
        return {
            "role": "system",
            "content": f"You are a testing agent making a voice call. "
            f"\nHave a conversation. Take a single turn at a time."
            f"\nDon't make sounds or any other subtext, only say words in conversation"
            f"\nThis is your persona:{self.eval_prompt}"
            "\nWhen conversation is complete, with final response return HANGUP to end."
            "\nEg: Have a good day. HANGUP"
            f"\nDate/time: {datetime_str}."
            "\nKeep responses short, under 20 words.",
        }

    @property
    def path(self):
        return get_info_path(
            self.project_id, self.version_id, self.eval_id, self.run_id, self.agent_id
        )

    def save(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        d = {
            "prompt": self.prompt,
            "eval_prompt": self.eval_prompt,
            "metric_names": self.metric_names,
            "history": self.history,
            "started": self.started,
            "ended": self.ended,
            "transcript": self.transcript,
            "scores": self.scores,
            "error": self.error,
        }
        save_json(d, self.path)

    @classmethod
    def load(cls, project_id, version_id, eval_id, run_id, agent_id):
        load_path = get_info_path(project_id, version_id, eval_id, run_id, agent_id)
        try:
            d = load_json(load_path)
        except FileNotFoundError:
            return

        d.update(
            {
                "project_id": project_id,
                "version_id": version_id,
                "eval_id": eval_id,
                "run_id": run_id,
                "agent_id": agent_id,
            }
        )
        return cls(**d)

    def evaluate(self, agent_class: Type["BaseAgent"], agent_starts: bool, **kwargs):
        agent = agent_class(**kwargs)
        if agent_starts is None:
            agent_starts = random.choice([True, False])

        if agent_starts:
            agent_message, ended = agent.respond("")
        else:
            agent_message, ended = "", False
        while 1:
            eval_agent_message, ended = self.respond(agent_message)
            if ended:
                break
            agent_message, ended = agent.respond(eval_agent_message)
            if ended:
                self.add_agent_message(agent_message)
                break

        self.handle_conversation_end()
