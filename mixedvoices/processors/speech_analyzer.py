from typing import List, Optional

from openai import OpenAI
from pydantic import BaseModel

import mixedvoices


# TODO: 2 step process, first LLM call will get steps,
# 2nd call will refine the steps according to the rules
class FlowChart(BaseModel):
    steps: List[str]


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
    existing_steps_context = ""
    if existing_step_names:
        existing_steps_string = ", ".join(existing_step_names)
        existing_steps_context = f"""Existing steps used in the project are:
        {existing_steps_string}.
        Reuse these exact steps verbatim if you encounter similar elements.
        Only reuse if the script has very similar elements.\n"""
    if mixedvoices.OPEN_AI_CLIENT is None:
        mixedvoices.OPEN_AI_CLIENT = OpenAI()

    client = mixedvoices.OPEN_AI_CLIENT
    try:
        completion = client.beta.chat.completions.parse(
            # model="gpt-4o-mini-2024-07-18",
            model="gpt-4o-2024-08-06",
            messages=[
                {
                    "role": "system",
                    "content": """You are an expert at analyzing transcripts and
                    breaking them down into essential, reusable flow chart steps. Your goal is to create
                    steps that can be used to analyze patterns across multiple similar interactions.""",  # noqa: E501
                },
                {
                    "role": "user",
                    "content": f"""Convert this transcript into 1-10 high-level steps.
                    Each step should represent a distinct phase, not individual exchanges.

                    Rules:
                    - Focus on the core progress of the interaction
                    - Each step should be 1-6 words and be self-explanatory
                    - Combine related exchanges into single meaningful steps
                    - Don't combine unrelated exchanges. Eg: Greeting shouldn't be combined with Inquiries.
                    - Steps should be broad enough to apply to similar interactions.
                    - Only add steps that provide additional information to the flow.

                    STANDARD STEPS TO USE when applicable:
                    - Greeting
                    - Determine Call Purpose
                    - Provide Business Information (use this instead of Provide Business Address/Timings, etc.)
                    - Collect Caller Information (use this instead of Collect Caller Name/Email, etc.)
                    - Request Expert Callback (use relevant variation of this like Request Technician/Dentist Callback)
                    - Schedule Appointment (use this instead of Determine Purpose/Schedule Appointment Date/Time/Location, etc.)
                    - Confirm Appointment Details (use this instead of Confirm Appointment Time/Location, etc.)
                    - Farewell

                    {existing_steps_context}
                    Transcript: {script}""",  # noqa: E501,
                },
            ],
            response_format=FlowChart,
        )

        return completion.choices[0].message.parsed.steps

    except Exception as e:
        print(f"Error processing script: {str(e)}")
        raise


# Example usage:
if __name__ == "__main__":
    sample_script = """bot: Hello this is Mary from Locoto Dental How can I assist you today
        user: Hello this is Abhinav I want to know the timings
        bot: Hey Abhinav we're open from 8am to 5pm Monday through Saturday closed on Sundays What can I do for you
        user: So I want to make an appointment
        bot: Great I'd be happy to help you with that Can I have your full name please
        user: I do not want to share my full name Will my first name suffice
        bot: Sure thing Abhinav What's the purpose of your appointment
        user: I want to have a root canal surgery
        bot: Ooh sounds like fun When would you like to come in Got it When would you like to schedule your root canal surgery
        user: Can we do it on Tuesday
        bot: Sure we can schedule you for Tuesday What time works best for you
        user: Anytime after 12 p m
        bot: Got it How about 2pm on Tuesday for your root canal surgery
        user: Yeah that should be
        bot: Alright Abhinav you're all set for your root canal surgery at 2pm on Tuesday Awesome
        user: good
        bot: Your appointment for a root canal surgery is booked for Tuesday at 2pm See you then
        user: All right bye bye
        bot: Bye bye See you soon
        user: Can you drop the call I do not have my phone in my hand I'm dry
        bot: Sure I'll disconnect the call now If you have any other questions feel free to call back See you on Tuesday
        user: You still haven't disconnected
        bot: Oh my bad Let me try that again Goodbye
        """  # noqa: E501

    existing_step_names = []

    try:
        steps = script_to_step_names(sample_script, existing_step_names)
        print("Generated steps:")
        for i, step in enumerate(steps, 1):
            print(f"{i}. {step}")
    except Exception as e:
        print(f"Failed to generate steps: {str(e)}")
