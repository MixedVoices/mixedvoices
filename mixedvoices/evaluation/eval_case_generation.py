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

STRUCTURE_PROMPT_MULTIPLE = """Give distinct prompts.
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

STRUCTURE_PROMPT_SINGLE = """Output structure below. Don't add blank lines b/w fields.
Prompts:-
----
Info: ..
Personality: ..
Call Objective: ..
Call Path: ..
----
"""

OUTPUT_PROMPT = "Prompts:-\n----"


def get_prompt_part(count):
    return (
        "a single TESTING agent prompt"
        if count == 1
        else f"{count} different TESTING agent prompts"
    )


def generate_eval_prompts(agent_prompt: str, generation_instruction: str, count: int):
    model = "gpt-4o"
    start_prompt = START_PROMPT.format(agent_prompt=agent_prompt)

    structure_prompt = (
        STRUCTURE_PROMPT_SINGLE if count == 1 else STRUCTURE_PROMPT_MULTIPLE
    )
    user_prompt = f"{start_prompt}\n{generation_instruction}\n{structure_prompt}"
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
    prompts = [p.strip() for p in prompts if len(p.strip()) > 50]
    assert len(prompts) == count  # TODO: Add retries
    return prompts


def generate_eval_prompts_for_failure_reasons(
    agent_prompt: str,
    failure_reasons: List[str],
    count: int = 2,
):
    eval_prompts = []
    for failure_reason in failure_reasons:
        part = get_prompt_part(count)
        instruction = (
            f"Generate {part} that try to recreate this failure: {failure_reason}"
        )
        eval_prompts.extend(generate_eval_prompts(agent_prompt, instruction, count))
    return eval_prompts


def generate_eval_prompts_for_new_paths(
    agent_prompt: str,
    new_paths: List[str],
    count: int = 2,
):
    eval_prompts = []
    for new_path in new_paths:
        part = get_prompt_part(count)
        instruction = f"Generate {part} that follow this path: {new_path}"  # noqa E501
        eval_prompts.extend(generate_eval_prompts(agent_prompt, instruction, count))
    return eval_prompts


def generate_eval_prompts_for_edge_cases(agent_prompt: str, count: int = 2):
    part = get_prompt_part(count)
    instruction = f"Generate {part} that simulate tricky edge cases."
    return generate_eval_prompts(agent_prompt, instruction, count)


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
