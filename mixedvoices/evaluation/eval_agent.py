import os
import random
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional, Tuple, Type

import mixedvoices as mv
import mixedvoices.constants as constants
from mixedvoices import models
from mixedvoices.evaluation.utils import history_to_transcript
from mixedvoices.metrics.metric import Metric
from mixedvoices.processors.llm_metrics import generate_scores
from mixedvoices.processors.success import get_success
from mixedvoices.utils import get_openai_client, load_json, save_json

if TYPE_CHECKING:
    from mixedvoices import BaseAgent  # pragma: no cover


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
        test_case,
        metric_names,
        history=None,
        started=False,
        ended=False,
        transcript=None,
        scores=None,
        is_successful=None,
        success_explanation=None,
        error=None,
    ):
        self.agent_id = agent_id
        self.project_id = project_id
        self.version_id = version_id
        self.eval_id = eval_id
        self.run_id = run_id

        self.prompt = prompt
        self.test_case = test_case
        self.metric_names = metric_names
        self.history = history or []
        self.started = started
        self.ended = ended
        self.transcript = transcript or None
        self.scores = scores or None
        self.is_successful = is_successful
        self.success_explanation = success_explanation
        self.error = error or None
        self.save()

    @property
    def metrics_and_success_criteria(self) -> Tuple[List[Metric], Optional[str]]:
        project = mv.load_project(self.project_id)
        return (
            project.get_metrics_by_names(self.metric_names),
            project._success_criteria,
        )

    def respond(self, input):
        if not self.started:
            self.started = True
            self.save()
        if input:
            self.add_agent_message(input)
        messages = [self.get_system_prompt()] + self.history
        try:
            client = get_openai_client()
            response = client.chat.completions.create(
                model=models.EVAL_AGENT_MODEL, messages=messages
            )
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
        metrics, success_criteria = self.metrics_and_success_criteria
        try:
            self.scores = generate_scores(
                self.transcript, self.prompt, metrics, success_criteria
            )
            print(self.scores)
            self.save()
        except Exception as e:
            self.handle_exception(e, "Metric Calculation")

        if success_criteria:
            try:
                response = get_success(self.transcript, success_criteria)
                self.is_successful = response["success"]
                self.success_explanation = response["explanation"]
                self.save()
            except Exception as e:
                self.handle_exception(e, "Success Criteria")

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
            f"\nThis is your persona:{self.test_case}"
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
            "test_case": self.test_case,
            "metric_names": self.metric_names,
            "history": self.history,
            "started": self.started,
            "ended": self.ended,
            "transcript": self.transcript,
            "is_successful": self.is_successful,
            "success_explanation": self.success_explanation,
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
