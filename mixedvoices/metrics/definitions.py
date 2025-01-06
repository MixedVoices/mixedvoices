from mixedvoices.metrics.metric import Metric

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
    "binary",
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
