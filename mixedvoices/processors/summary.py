from mixedvoices.processors.utils import get_openai_client


def summarize_transcript(transcript: str):
    client = get_openai_client()
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": "You're an expert at summarizing transcripts into short paragraphs. Keep the summary under 200 words.",
            },
            {"role": "user", "content": transcript},
            {"role": "assistant", "content": "Summary:-"},
        ],
    )
    return response.choices[0].message.content
