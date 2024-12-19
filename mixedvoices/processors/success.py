from mixedvoices.processors.utils import get_openai_client, parse_explanation_response


# TODO check for prompt injection
def get_success(transcript: str, success_criteria: str):
    client = get_openai_client()
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You're an expert at assessing whether a call b/w human and AI was successful. "
                    "Output a short explanation in under 5 words along with TRUE or FALSE or N/A",
                },
                {
                    "role": "user",
                    "content": f"""
                    Transcript:
                    ---
                    {transcript}
                    ---

                    Success Criteria:
                    ---
                    {success_criteria}
                    ---

                    Format example

                    Output:-
                    Explanation: Lorem ipsum
                    Success: TRUE or FALSE or N/A
                    """,
                },
                {"role": "assistant", "content": "Output:-"},
            ],
        )
        return parse_explanation_response(response.choices[0].message.content)
    except Exception as e:
        print(f"Error analyzing metric: {e}")
        return {"explanation": "Analysis failed", "success": "N/A"}
