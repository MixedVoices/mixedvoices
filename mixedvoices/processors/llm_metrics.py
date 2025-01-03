from typing import List

from mixedvoices import models
from mixedvoices.metrics.metric import Metric
from mixedvoices.processors.utils import parse_explanation_response
from mixedvoices.utils import get_openai_client


def analyze_metric(transcript: str, prompt: str, metric: Metric):
    metric_name = metric.name
    metric_definition = metric.definition
    expected_values = metric.expected_values

    metric_definition += f"\nExpected Score Values: {expected_values}"

    if metric.include_prompt:
        metric_definition = f"{metric_definition}\nPrompt: {prompt}"

    client = get_openai_client()
    prompt = f"""Transcript:
    {transcript}

    Respond with short 1 line explanation of how the bot performed on {metric_name}, followed by score. 
    Metric:
    {metric_definition}
    >Format example

    Output:-
    Explanation: Lorem ipsum
    Score:
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

            result = parse_explanation_response(response.choices[0].message.content)
            if result["score"] in expected_values:
                return result
            raise ValueError(f"Unexpected score: {result['score']}")
        except ValueError as e:
            print(f"Error parsing metric: {e}")
        except Exception as e:
            print(f"Error analyzing metric: {e}")
            return {"explanation": "Analysis failed", "score": "N/A"}


def generate_scores(transcript: str, prompt: str, metrics: List[Metric]):
    return {m.name: analyze_metric(transcript, prompt, m) for m in metrics}
