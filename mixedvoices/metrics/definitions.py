"""Predefined metrics for evaluating conversational agent performance.

This module contains default metrics used to evaluate different aspects of 
conversational agent behavior, from empathy to technical accuracy.
"""

from mixedvoices.metrics.metric import Metric

empathy = Metric(
    "Empathy",
    "Did the bot answer all the questions empathically? Empathy includes answering a question by acknowledging what user said, empathising by relating to their pain, repeating some of the user's words back to make them feel heard before answering a question.",
    "continuous",
)
"""Name: Empathy
Defintion: Did the bot answer all the questions empathically? Empathy includes answering a question by acknowledging what user said, empathising by relating to their pain, repeating some of the user's words back to make them feel heard before answering a question.
Scoring: continuous
Include Prompt: False
"""

verbatim_repetition = Metric(
    "Verbatim Repetition",
    "Did the bot repeat itself verbatim when asked the same/similar question? Similar answers are not repetition.",
    "binary",
)
"""Name: Verbatim Repetition
Definition: Did the bot repeat itself verbatim when asked the same/similar question? Similar answers are not repetition.
Scoring: binary
Include Prompt: False
"""

conciseness = Metric(
    "Conciseness",
    "Did the bot concisely answer the questions/objections? Concise answers should be less than 50 words.",
    "continuous",
)
"""Name: Conciseness
Definition: Did the bot concisely answer the questions/objections? Concise answers should be less than 50 words.
Scoring: continuous
Include Prompt: False
"""

hallucination = Metric(
    "Hallucination",
    "Does the bot answer any question with information that isn't present in the prompt?",
    "binary",
    True,
)
"""Name: Hallucination
Definition: Does the bot answer any question with information that isn't present in the prompt?
Scoring: binary
Include Prompt: True
"""

context_awareness = Metric(
    "Context Awareness",
    "Does the bot maintain awareness of the context/information provided by user? The bot should make its answers contextual by acknowledging what the user said and customizing its responses.",
    "binary",
)
"""Name: Context Awareness
Definition: Does the bot maintain awareness of the context/information provided by user? The bot should make its answers contextual by acknowledging what the user said and customizing its responses.
Scoring: binary
Include Prompt: False
"""

scheduling = Metric(
    "Scheduling",
    "Does the bot properly schedule appointments? This includes asking for relevant information, figuring out date and time, and confirming with the user.",
    "continuous",
)
"""Name: Scheduling
Definition: Does the bot properly schedule appointments? This includes asking for relevant information, figuring out date and time, and confirming with the user.
Scoring: continuous
Include Prompt: False
"""

adaptive_qa = Metric(
    "Adaptive QA",
    "Does the bot only ask questions related to the current topic? Also, it shouldn't ask a question that has already been answered by the user.",
    "continuous",
)
"""Name: Adaptive QA
Definition: Does the bot only ask questions related to the current topic? Also, it shouldn't ask a question that has already been answered by the user.
Scoring: continuous
Include Prompt: False
"""

objection_handling = Metric(
    "Objection Handling",
    "Does the bot acknowledge objections, relate to the user's concern in a way that sympathizes with their pain, and offer relevant solutions? Bad examples i.e. low scores: The bot skips acknowledging the concern, uses generic sales language without empathizing, or offers an irrelevant or off-topic response.",
    "continuous",
)
"""Name: Objection Handling
Definition: Does the bot acknowledge objections, relate to the user's concern in a way that sympathizes with their pain, and offer relevant solutions? Bad examples i.e. low scores: The bot skips acknowledging the concern, uses generic sales language without empathizing, or offers an irrelevant or off-topic response.
Scoring: continuous
Include Prompt: False
"""


def get_all_default_metrics() -> list[Metric]:
    """Returns a list of all default metrics available in the system.

    These metrics cover various aspects of conversational agent performance:
    - Emotional intelligence (empathy, objection handling)
    - Technical accuracy (hallucination, verbatim repetition)
    - Conversation quality (conciseness, context awareness)
    - Task completion (scheduling, adaptive QA)

    Example:
        >>> metrics = get_all_default_metrics()
        >>> for metric in metrics:
        ...     print(f"{metric.name}: {metric.scoring}")
        Empathy: continuous
        Verbatim Repetition: binary
        ...
    """
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
