from typing import List, Optional

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
            model="gpt-4o",
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
        steps = [step.strip() for step in final_steps_section.split(",")]

        return steps
    except Exception as e:
        print(f"Error processing script: {str(e)}")
        raise


# Example usage:
if __name__ == "__main__":
    sample_script_1 = """bot: Hello this is Mary from Locoto Dental How can I assist you today
        1. user: Hello this is Abhinav I want to know the timings
        2. bot: Hey Abhinav we're open from 8am to 5pm Monday through Saturday closed on Sundays What can I do for you
        3. user: So I want to make an appointment
        4. bot: Great I'd be happy to help you with that Can I have your full name please
        5. user: I do not want to share my full name Will my first name suffice
        6. bot: Sure thing Abhinav What's the purpose of your appointment
        7. user: I want to have a root canal surgery
        8. bot: Ooh sounds like fun When would you like to come in Got it When would you like to schedule your root canal surgery
        9. user: Can we do it on Tuesday
        10. bot: Sure we can schedule you for Tuesday What time works best for you
        11. user: Anytime after 12 p m
        12. bot: Got it How about 2pm on Tuesday for your root canal surgery
        13. user: Yeah that should be
        14. bot: Alright Abhinav you're all set for your root canal surgery at 2pm on Tuesday Awesome
        15. user: good
        16. bot: Your appointment for a root canal surgery is booked for Tuesday at 2pm See you then
        17. user: All right bye bye
        18. bot: Bye bye See you soon
        19. user: Can you drop the call I do not have my phone in my hand I'm dry
        20. bot: Sure I'll disconnect the call now If you have any other questions feel free to call back See you on Tuesday
        21. user: You still haven't disconnected
        22. bot: Oh my bad Let me try that again Goodbye
        """  # noqa: E501

    sample_script_2 = """
            1. bot: Hi. Thank you for calling MixedVoices Dealership. How can I help?
            2. user: Hi. The light came on on my car, and it says that I need more oil. Can I buy motor oil at the store there to top up my car.  
            3. bot: I'd be happy to help you with that. Can you please provide the year and model of your car?  
            4. user: It's a twenty twenty two Jetta.
            5. bot: Thank you for that information. Please hold on while I check our inventory for motor oil for your twenty twenty two Jetta. I have good news. We have motor oil in stock. Is there anything else I can assist you with?  
            6. user: No. That's it. Uh, thanks for the good news.
            7. bot: You're welcome. I'm glad I could help. Have a great day.
            8. user: Bye.
            9. bot: Goodbye.
            """  # noqa: E501

    existing_step_names = []

    try:
        steps = script_to_step_names(sample_script_2, existing_step_names)
        print("Generated steps:")
        for i, step in enumerate(steps, 1):
            print(f"{i}. {step}")
    except Exception as e:
        print(f"Failed to generate steps: {str(e)}")
