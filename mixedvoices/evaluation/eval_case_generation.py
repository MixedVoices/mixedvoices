from typing import List

from mixedvoices.utils import get_openai_client

SYSTEM_PROMPT = """You're an expert at creating PROMPTS for TESTING agents to evaluate REAL agent.
    Prompt Structure (Each field should be inline, no bullets/numbers):-
    Info i.e name and age for eg. John Doe, 30
    Personality i.e. Talking style, quirks, 1-2 lines, don't use terms like Type A/B etc. Don't include speed, pauses, modulation, this is text only.
    Call Objective 1-3 lines, include who you are calling here as well
    Call Path, represent like A->B->C..->Farewell where A, B, C are steps, ALWAYS end with Farewell
    """  # noqa E501

START_PROMPT = """REAL agent prompt:
----
{agent_prompt}
----"""

STRUCTURE_PROMPT = """Give distinct prompts.
Output structure below. Don't add blank lines b/w fields.
Prompts:-
----
Info: ..
Personality: ..
Call Objective: ..
Call Path: ..
----
Info: ..
Personality: ..
Call Objective: ..
Call Path: ..
----
and so on
"""

OUTPUT_PROMPT = "Prompts:-\n----"


def generate_eval_prompts(agent_prompt: str, generation_instruction: str):
    model = "gpt-4o"
    start_prompt = START_PROMPT.format(agent_prompt=agent_prompt)
    user_prompt = f"{start_prompt}\n{generation_instruction}\n{STRUCTURE_PROMPT}"
    client = get_openai_client()
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
            {"role": "assistant", "content": OUTPUT_PROMPT},
        ],
    )
    response_text = completion.choices[0].message.content
    prompts = response_text.split("----")
    return [p.strip() for p in prompts if len(p.strip()) > 50]


def generate_eval_prompts_for_failure_reasons(
    agent_prompt: str,
    failure_reasons: List[str],
    count: int = 2,
):
    eval_prompts = []
    for failure_reason in failure_reasons:
        instruction = f"Generate {count} different TESTING agent prompts that try to recreate this failure: {failure_reason}"  # noqa E501
        eval_prompts.extend(generate_eval_prompts(agent_prompt, instruction))
    return eval_prompts


def generate_eval_prompts_for_new_paths(
    agent_prompt: str,
    new_paths: List[str],
    count: int = 2,
):
    eval_prompts = []
    for new_path in new_paths:
        instruction = f"Generate {count} different TESTING agent prompts that follow this path: {new_path}"  # noqa E501
        eval_prompts.extend(generate_eval_prompts(agent_prompt, instruction))
    return eval_prompts


def generate_eval_prompts_for_edge_cases(agent_prompt: str, count: int = 2):
    instruction = f"Generate {count} different TESTING agent prompts that simulate tricky edge cases."  # noqa E501
    return generate_eval_prompts(agent_prompt, instruction)


def get_eval_prompts(
    agent_prompt: str,
    failure_reasons: List[str],
    new_paths: List[str],
    test_cases_per_path: int,
    test_cases_per_failure_reason: int,
    total_test_cases_for_edge_scenarios: int,
):
    new_path_prompts = generate_eval_prompts_for_new_paths(
        agent_prompt, new_paths, test_cases_per_path
    )
    failure_prompts = generate_eval_prompts_for_failure_reasons(
        agent_prompt, failure_reasons, test_cases_per_failure_reason
    )
    edge_case_prompts = generate_eval_prompts_for_edge_cases(
        agent_prompt, total_test_cases_for_edge_scenarios
    )
    return new_path_prompts + failure_prompts + edge_case_prompts


if __name__ == "__main__":
    # TODO: Move this to tests
    agent_prompt = """You are a voice assistant for Locoto's Dental, a dental office located at 123 North Face Place, Anaheim, California. The hours are 8 AM to 5PM daily, but they are closed on Sundays.

    Locoto's dental provides dental services to the local Anaheim community. The practicing dentist is Dr. Mary Smith.

    You are tasked with answering questions about the business, and booking appointments. If they wish to book an appointment, your goal is to gather necessary information from callers in a friendly and efficient manner like follows:

    1. Ask for their full name.
    2. Ask for the purpose of their appointment.
    3. Request their preferred date and time for the appointment.
    4. Confirm all details with the caller, including the date and time of the appointment.

    - Be sure to be kind of funny and witty!
    - Keep all your responses short and simple. Use casual language, phrases like "Umm...", "Well...", and "I mean" are preferred.
    - This is a voice conversation, so keep your responses short, like in a real conversation. Don't ramble for too long.
    """  # noqa E501

    new_paths = [
        "Greeting->Determine Call Purpose->Provide Business Information->Farewell"
    ]
    failure_reasons = ["Bot doesn't know what day/time it is currently"]

    eval_prompts = get_eval_prompts(agent_prompt, failure_reasons, new_paths, 2, 2, 2)

    for i, prompt in enumerate(eval_prompts):
        print(f"Prompt {i}: {prompt}")
