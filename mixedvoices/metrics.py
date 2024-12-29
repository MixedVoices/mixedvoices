from dataclasses import dataclass
from typing import Literal

# TODO: add more metrics, define better
# TODO: allow creation of custom call metrics

@dataclass
class Metric:
    name: str
    definition: str
    scoring: Literal["binary", "continuous"]
    include_prompt: bool = False

    @property
    def expected_values(self):
        if self.scoring == "binary":
            return ["PASS", "FAIL", "N/A"]
        elif self.scoring == "continuous":
            return list(range(11)) + ["N/A"]

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"Metric(name='{self.name}', scoring_range={self.scoring})"

    def to_dict(self):
        return {
            "name": self.name,
            "definition": self.definition,
            "scoring": self.scoring,
            "include_prompt": self.include_prompt,
        }


def serialize_metrics(metrics: list[Metric]):
    return [metric.to_dict() for metric in metrics]


def deserialize_metrics(metrics: list[dict]):
    return [Metric(**metric) for metric in metrics]


empathy = Metric(
    "Empathy",
    "Did the bot, answer all the questions empathically? Empathy includes answering a question by acknowledging what user said, empathising by relating to their pain, repeating some of the user's words back to make them feel heard before answering a question.",
    "continuous",
)

verbatim_repetition = Metric(
    "Verbatim Repetition",
    "Did the bot repeat itself verbatim when asked the same/similar question? Similar answers are not repetition.",
    "binary",
)

conciseness = Metric(
    "Conciseness",
    "Did the bot concisely answe the questions/objections? Concise answers should be less than 50 words.",
    "continuous",
)

hallucination = Metric(
    "Hallucination",
    "Does the bot answer any question with information that isn't present in the prompt?",
    "binary",
    True,
)

context_awareness = Metric(
    "Context Awareness",
    "Does the bot maintain awareness of the context/information provided by user? The bot should make its answers contextual by acknowledging what the user said and customizing its responses.",
    ["PASS", "FAIL"],
)

scheduling = Metric(
    "Scheduling",
    "Does the bot properly schedule appointments? This includes asking for relevant information, figuring out date and time, and confirming with the user.",
    "continuous",
)

adaptive_qa = Metric(
    "Adaptive QA",
    "Does the bot only ask questions related to the current topic? Also, it shouldn't ask a question that has already been answered by the user.",
    "continuous",
)

objection_handling = Metric(
    "Objection Handling",
    "Does the bot acknowledge objections, relate to the user's concern in a way that sympathizes with their pain, and offer relevant solutions? Bad examples i.e. low scores: The bot skips acknowledging the concern, uses generic sales language without empathizing, or offers an irrelevant or off-topic response.",
    "continuous",
)


def get_all_default_metrics() -> list[Metric]:
    return [
        empathy,
        verbatim_repetition,
        conciseness,
        hallucination,
        context_awareness,
        scheduling,
        adaptive_qa,
        objection_handling,
    ]
