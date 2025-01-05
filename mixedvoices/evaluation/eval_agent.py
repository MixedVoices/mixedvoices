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


# TODO: Better logging
# TODO: Show error in dashboard if there is one
class EvalAgent:
    def __init__(
        self,
        agent_id: str,
        project_id: str,
        version_id: str,
        eval_id: str,
        run_id: str,
        agent_prompt: str,
        test_case: str,
        metric_names: List[str],
        verbose: bool = True,
        history: Optional[List[dict]] = None,
        started: bool = False,
        ended: bool = False,
        transcript: Optional[str] = None,
        scores: Optional[dict] = None,
        is_successful: Optional[bool] = None,
        success_explanation: Optional[str] = None,
        error: Optional[str] = None,
    ):
        self._agent_id = agent_id
        self._project_id = project_id
        self._version_id = version_id
        self._eval_id = eval_id
        self._run_id = run_id

        self._agent_prompt = agent_prompt
        self._test_case = test_case
        self._metric_names = metric_names
        self._verbose = verbose
        self._history = history or []
        self._started = started
        self._ended = ended
        self._transcript = transcript or None
        self._scores = scores or None
        self._is_successful = is_successful
        self._success_explanation = success_explanation
        self._error = error or None
        self._save()

    def _print_header(self, title, test_case_num):
        print("\n\n")
        print("=" * 100)
        print(f" Test Case #{test_case_num}: {title} ".center(100, "="))
        print("=" * 100)
        print("\n")

    def _print_section(self, title):
        print("\n" + "-" * 40)
        print(f" {title} ")
        print("-" * 40)

    @property
    def id(self):
        """Get id of the EvalAgent"""
        return self._agent_id

    @property
    def project_id(self):
        """Get the name of the Project"""
        return self._project_id

    @property
    def version_id(self):
        """Get the name of the Version"""
        return self._version_id

    @property
    def eval_id(self):
        """Get the id of the Evaluator"""
        return self._eval_id

    @property
    def run_id(self):
        """Get the name of the EvalRun"""
        return self._run_id

    def evaluate(
        self,
        agent_class: Type["BaseAgent"],
        agent_starts: bool,
        test_case_num: int,
        **kwargs,
    ):
        """Evaluates the agent on the test case"""
        if self._verbose:
            self._print_header("Evaluation", test_case_num)
            self._print_section("Test Case Details")
            print(f"Description: {self._test_case}\n")
            self._print_section("Conversation")

        try:
            agent = agent_class(**kwargs)
            if agent_starts is None:
                agent_starts = random.choice([True, False])

            if agent_starts:
                agent_message, ended = agent.respond("")
            else:
                agent_message, ended = "", False

            while 1:
                eval_agent_message, ended = self._respond(agent_message)
                if ended:
                    break
                agent_message, ended = agent.respond(eval_agent_message)
                if ended:
                    self._add_agent_message(agent_message)
                    break

            self._handle_conversation_end()
        except Exception as e:
            self._handle_exception(e, "evaluate")

    def results(self):
        """Returns the results of the agent as a dictionary"""
        return {
            "test_case": self._test_case,
            "started": self._started,
            "ended": self._ended,
            "transcript": self._transcript,
            "scores": self._scores,
            "is_successful": self._is_successful,
            "success_explanation": self._success_explanation,
            "error": self._error,
        }

    @property
    def status(self):
        """Returns the status of the agent as a string"""
        if not self._started:
            return "PENDING"
        if self._error:
            return "FAILED"
        return "COMPLETED" if self._ended else "IN PROGRESS"

    def _get_metrics_and_success_criteria(self) -> Tuple[List[Metric], Optional[str]]:
        project = mv.load_project(self.project_id)
        return (
            project.get_metrics_by_names(self._metric_names),
            project._success_criteria,
        )

    def _respond(self, input: Optional[str]):
        if not self._started:
            self._started = True
            self._save()
        if input:
            self._add_agent_message(input)
        messages = [self._get_system_prompt()] + self._history
        try:
            client = get_openai_client()
            response = client.chat.completions.create(
                model=models.EVAL_AGENT_MODEL, messages=messages
            )
            evaluator_response = response.choices[0].message.content
            self._add_eval_agent_message(evaluator_response)
            return evaluator_response, has_ended_conversation(evaluator_response)
        except Exception as e:
            self._handle_exception(e, "Conversation")

    def _add_agent_message(self, message: str):
        self._history.append({"role": "user", "content": message})
        if self._verbose:
            print(f"\nAgent    : {message}")

    def _add_eval_agent_message(self, message: str):
        self._history.append({"role": "assistant", "content": message})
        if self._verbose:
            print(f"\nEvaluator: {message}")

    def _handle_conversation_end(self):
        self._ended = True
        self._transcript = history_to_transcript(self._history)
        metrics, success_criteria = self._get_metrics_and_success_criteria()
        try:
            self._scores = generate_scores(
                self._transcript, self._agent_prompt, metrics
            )
            if self._verbose:
                self._print_section("Evaluation Scores")
                for metric_name, score_dict in self._scores.items():
                    print(f"\n{metric_name.title()}:")
                    print(f"Score      : {score_dict['score']}")
                    print(f"Explanation: {score_dict['explanation']}")

            self._save()
        except Exception as e:
            self._handle_exception(e, "Metric Calculation")

        if success_criteria:
            try:
                response = get_success(self._transcript, success_criteria)
                self._is_successful = response["success"]
                self._success_explanation = response["explanation"]
                if self._verbose:
                    self._print_section("Success Criteria")
                    print(f"\nSuccess    : {self._is_successful}")
                    print(f"Explanation: {self._success_explanation}")
                self._save()
            except Exception as e:
                self._handle_exception(e, "Success Criteria")

    def _handle_exception(self, e, source):
        self._error = f"Error Source: EvalAgent {source} \nError: {str(e)}"
        self._ended = True
        self._transcript = self._transcript or history_to_transcript(self._history)
        self._save()
        if source == "evaluate":
            raise e

    def _get_system_prompt(self):
        datetime_str = datetime.now().strftime("%I%p, %a, %d %b").lower().lstrip("0")
        return {
            "role": "system",
            "content": f"You are a testing agent making a voice call. "
            f"\nHave a conversation. Take a single turn at a time."
            f"\nDon't make sounds or any other subtext, only say words in conversation"
            f"\nThis is your persona:{self._test_case}"
            "\nWhen conversation is complete, with final response return HANGUP to end."
            "\nEg: Have a good day. HANGUP"
            f"\nDate/time: {datetime_str}."
            "\nKeep responses short, under 20 words.",
        }

    @property
    def _path(self):
        return get_info_path(
            self.project_id,
            self.version_id,
            self.eval_id,
            self.run_id,
            self.id,
        )

    def _save(self):
        os.makedirs(os.path.dirname(self._path), exist_ok=True)
        d = {
            "agent_prompt": self._agent_prompt,
            "test_case": self._test_case,
            "metric_names": self._metric_names,
            "history": self._history,
            "started": self._started,
            "ended": self._ended,
            "transcript": self._transcript,
            "is_successful": self._is_successful,
            "success_explanation": self._success_explanation,
            "scores": self._scores,
            "error": self._error,
        }
        save_json(d, self._path)

    @classmethod
    def _load(cls, project_id, version_id, eval_id, run_id, agent_id):
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
