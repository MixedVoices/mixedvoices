from typing import List, Optional

from mixedvoices import models
from mixedvoices.processors.utils import get_standard_steps_string
from mixedvoices.utils import get_openai_client


def script_to_step_names(
    script: str, existing_step_names: Optional[List[str]] = None
) -> List[str]:
    """
    Convert a script into a concise series of flow chart steps using OpenAI's API.
    Args:
        script (str): The input script/transcript to convert
        existing_step_names (List[str], optional): List of existing steps to reuse
    Returns:
        List[str]: Ordered list of steps for the flow chart
    """
    standard_steps_list_str = get_standard_steps_string(existing_step_names)
    client = get_openai_client()
    try:
        completion = client.chat.completions.create(
            model=models.STEPS_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You're an expert at analyzing transcripts and "
                    "breaking them into essential, reusable flow chart steps. "
                    "GOAL: create steps that can be used to analyze "
                    "patterns across multiple transcripts.",
                },
                {
                    "role": "system",
                    "content": f"""Rules for creating steps:
                    - Focus on the core flow
                    - 1-6 words and self-explanatory name
                    - Combine related exchanges into single meaningful steps
                    - Broad enough to apply to similar interactions
                    - Only add steps that provide useful info

                    SHOW YOUR WORK:

                    #Thinking#
                    STEP BREAKDOWN
                    Identify steps in the flow and for each:
                    Step Name
                    a)Consecutive line numbers in the transcript eg. 5-7
                    b)Mention whether step is (NEW/REUSED from STANDARD STEP Number X)
                    c)If REUSED:
                    - Ensure that it is only being reused if the exact meaning is same
                    OR
                    c)If NEW:
                    - Briefly explain why step is generic, applicable to similar interactions

                    EXAMPLE:
                    1. Greeting
                    a) 1-3
                    b) REUSED from 1
                    c) Yes, hello hi has same meaning

                    #Output#
                    Use the thinking to list final step names in order, comma separated

                    STANDARD STEPS TO USE *ONLY when applicable*
                    (the subpoints are just explanations)

                    {standard_steps_list_str}
                    """,
                },
                {
                    "role": "user",
                    "content": f"Transcript: {script}",
                },
                {
                    "role": "assistant",
                    "content": "#Thinking#",
                },
            ],
            temperature=0,
        )

        response_text = completion.choices[0].message.content
        final_steps_section = response_text.split("#Output#")[-1].strip()
        return [step.strip() for step in final_steps_section.split(",")]
    except Exception as e:
        print(f"Error processing script: {str(e)}")
        raise
