from mixedvoices import models
from mixedvoices.utils import get_openai_client


def summarize_transcript(transcript: str):
    client = get_openai_client()
    response = client.chat.completions.create(
        model=models.SUMMARY_MODEL,
        messages=[
            {
                "role": "system",
                "content": "You're an expert note taker. "
                "Summarize given transcript in 2-3 sentences.",
            },
            {"role": "user", "content": f"Transcript: {transcript}"},
            {"role": "assistant", "content": "Summary:-"},
        ],
    )
    return response.choices[0].message.content
