from mixedvoices import models
from mixedvoices.processors.utils import parse_explanation_response
from mixedvoices.utils import get_openai_client


# TODO: add more metrics, define better
def analyze_metric(transcript: str, metric_name: str, metric_definition: str):
    client = get_openai_client()
    prompt = f"""Transcript:
    {transcript}

    Respond with short 1 line explanation of how the bot performed on {metric_name}, followed by score. 
    Metric:
    {metric_definition}
    >Format example

    Output:-
    Explanation: Lorem ipsum
    Score: 6
    """  # noqa E501

    num_tries = 3
    for _ in range(num_tries):
        try:
            response = client.chat.completions.create(
                model=models.METRICS_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You're an expert at analyzing transcripts",  # noqa E501,
                    },
                    {"role": "user", "content": prompt},
                    {"role": "assistant", "content": "Output:-"},
                ],
            )

            return parse_explanation_response(response.choices[0].message.content)
        except ValueError as e:
            print(f"Error parsing metric: {e}")
        except Exception as e:
            print(f"Error analyzing metric: {e}")
            return {"explanation": "Analysis failed", "score": "N/A"}


def analyze_empathy(transcript: str):
    metric_name = "Empathy"
    metric_definition = """Did the bot, answer all the questions empathically?
      Empathy includes answering a question by acknowledging what user said,
      empathising by relating to their pain, repeating some of the user's words
      back to make them feel heard before answering a question.
      Scoring: 0 to 10. 10 being the best.
    """

    return analyze_metric(transcript, metric_name, metric_definition)


def analyze_verbatim_repetition(transcript: str):
    metric_name = "Verbatim Repetition"
    metric_definition = """
    Did the bot repeat itself verbatim when asked the same/similar question?
    Similar answers are not repetition.
    Scoring: FAIL if it repeated VERBATIM for any question, PASS if never repeated, N/A if didn't encounter similar questions.
    """  # noqa E501

    return analyze_metric(transcript, metric_name, metric_definition)


def analyze_conciseness(transcript: str):
    metric_name = "Conciseness"
    metric_definition = """Did the bot concisely answe the questions/objections? Concise answers should be less than 50 words.
    Scoring: 0 to 10. 10 being the best.
    """  # noqa E501

    return analyze_metric(transcript, metric_name, metric_definition)


def analyze_hallucination(transcript: str, prompt: str):
    metric_name = "Hallucination"
    metric_definition = f"""Does the bot answer any question with information that isn't present in the prompt?
    Scoring: FAIL if it hallucinated, PASS if it didn't hallucinate.

    Prompt:
    {prompt}
    """  # noqa E501

    return analyze_metric(transcript, metric_name, metric_definition)


def analyze_context_awareness(transcript: str):
    metric_name = "Context Awareness"
    metric_definition = """Does the bot maintain awareness of the context/information provided by user?
    The bot should make its answers contextual by acknowledging what the user said and customizing its responses.
    Scoring: FAIL if it loses context, PASS if it maintains context.
    """  # noqa E501

    return analyze_metric(transcript, metric_name, metric_definition)


def analyze_scheduling(transcript: str):
    metric_name = "Scheduling"
    metric_definition = """Does the bot properly schedule appointments? 
    This includes asking for relevant information, figuring out date and time, and confirming with the user.
    Scoring: 0 to 10. 10 being the best. N/A if no scheduling is involved
    """  # noqa E501

    return analyze_metric(transcript, metric_name, metric_definition)


def analyze_adaptive_qa(transcript: str):
    metric_name = "Adaptive QA"
    metric_definition = """Does the bot only ask questions related to the current topic?
    Also, it shouldn't ask a question that has already been answered by the user.
    Scoring: 0 to 10. 10 being the best.
    """

    return analyze_metric(transcript, metric_name, metric_definition)


def analyze_objection_handling(transcript: str):
    metric_name = "Objection Handling"
    metric_definition = """
    Does the bot acknowledge objections, relate to the user's concern in a way that sympathizes with their pain, and offer relevant solutions?
    Bad examples i.e. low scores: The bot skips acknowledging the concern, uses generic sales language without empathizing, or offers an irrelevant or off-topic response.
    Scoring: 0 to 10. N/A if no objections are involved
    """  # noqa E501

    return analyze_metric(transcript, metric_name, metric_definition)


def get_llm_metrics(
    transcript: str,
    prompt: str,
    empathy: bool = True,
    verbatim_repetition: bool = True,
    conciseness: bool = True,
    hallucination: bool = True,
    context_awareness: bool = True,
    scheduling: bool = True,
    adaptive_qa: bool = True,
    objection_handling: bool = True,
):
    results = {}
    if empathy:
        results["empathy"] = analyze_empathy(transcript)
    if verbatim_repetition:
        results["repetition"] = analyze_verbatim_repetition(transcript)
    if conciseness:
        results["conciseness"] = analyze_conciseness(transcript)
    if hallucination:
        results["hallucination"] = analyze_hallucination(transcript, prompt)
    if context_awareness:
        results["context"] = analyze_context_awareness(transcript)
    if scheduling:
        results["scheduling"] = analyze_scheduling(transcript)
    if adaptive_qa:
        results["adaptive_qa"] = analyze_adaptive_qa(transcript)
    if objection_handling:
        results["objection_handling"] = analyze_objection_handling(transcript)
    return results
