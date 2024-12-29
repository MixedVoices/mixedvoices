from typing import TYPE_CHECKING, List, Optional

from mixedvoices.utils import get_openai_client

if TYPE_CHECKING:
    from mixedvoices.core.project import Project  # pragma: no cover
    from mixedvoices.core.version import Version  # pragma: no cover

# TODO: This style doesn't encapsulate transcription errors
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

DEMOGRAPHIC_PROMPT = """User Demographic (try to simulate such personalities and info)
----
{user_demographic_info}
----
"""

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


def generate_eval_prompts(
    agent_prompt: str,
    generation_instruction: str,
    count: int,
    user_demographic_info: Optional[str] = None,
):
    model = "gpt-4o"
    start_prompt = START_PROMPT.format(agent_prompt=agent_prompt)

    structure_prompt = (
        STRUCTURE_PROMPT_SINGLE if count == 1 else STRUCTURE_PROMPT_MULTIPLE
    )
    user_prompt = f"{start_prompt}\n{generation_instruction}\n{structure_prompt}"
    client = get_openai_client()
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]
    if user_demographic_info:
        demographic_prompt = DEMOGRAPHIC_PROMPT.format(
            user_demographic_info=user_demographic_info
        )
        messages.append({"role": "user", "content": demographic_prompt})

    messages.append({"role": "assistant", "content": OUTPUT_PROMPT})
    completion = client.chat.completions.create(
        model=model,
        messages=messages,
    )
    response_text = completion.choices[0].message.content
    prompts = response_text.split("----")
    prompts = [p.strip() for p in prompts if len(p.strip()) > 50]
    assert len(prompts) == count  # TODO: Add retries
    return prompts


# TODO: Use this in future
def generate_eval_prompts_for_failure_reasons(
    agent_prompt: str,
    failure_reasons: List[str],
    count: int = 2,
    user_demographic_info: Optional[str] = None,
):
    eval_prompts = []
    for failure_reason in failure_reasons:
        part = get_prompt_part(count)
        instruction = (
            f"Generate {part} that try to recreate this failure: {failure_reason}"
        )
        eval_prompts.extend(
            generate_eval_prompts(
                agent_prompt, instruction, count, user_demographic_info
            )
        )
    return eval_prompts


def generate_eval_prompts_from_paths(
    agent_prompt: str,
    paths: List[str],
    count_per_path=2,
    user_demographic_info: Optional[str] = None,
):
    eval_prompts = []
    for path in paths:
        part = get_prompt_part(count_per_path)
        instruction = f"Generate {part} that follow this path: {path}"  # noqa E501
        eval_prompts.extend(
            generate_eval_prompts(
                agent_prompt, instruction, count_per_path, user_demographic_info
            )
        )
    return eval_prompts


def generate_eval_prompts_from_version(
    agent_prompt: str,
    version: "Version",
    count_per_path=2,
    user_demographic_info: Optional[str] = None,
):
    paths = version.get_paths()
    return generate_eval_prompts_from_paths(
        agent_prompt, paths, count_per_path, user_demographic_info
    )


def generate_eval_prompts_from_project(
    agent_prompt: str,
    project: "Project",
    count_per_path=2,
    user_demographic_info: Optional[str] = None,
):
    paths = project.get_paths()
    return generate_eval_prompts_from_paths(
        agent_prompt, paths, count_per_path, user_demographic_info
    )


def generate_eval_prompts_for_edge_cases(
    agent_prompt: str,
    count: int = 2,
    user_demographic_info: Optional[str] = None,
):
    part = get_prompt_part(count)
    instruction = f"Generate {part} that simulate tricky edge cases."
    return generate_eval_prompts(
        agent_prompt, instruction, count, user_demographic_info
    )


def generate_eval_prompts_from_transcripts(
    agent_prompt: str,
    transcripts: List[str],
    count: int = 1,
    user_demographic_info: Optional[str] = None,
):
    eval_prompts = []
    for transcript in transcripts:
        part = get_prompt_part(count)
        instruction = f"Generate {part} that try to recreate this transcript: {transcript}"  # noqa E501
        eval_prompts.extend(
            generate_eval_prompts(
                agent_prompt, instruction, count, user_demographic_info
            )
        )
    return eval_prompts


def generate_eval_prompts_from_recording(
    agent_prompt: str,
    recording_paths: List[str],
    user_demographic_info: Optional[str] = None,
):
    transcripts = recording_paths  # TODO: Add transcription
    return generate_eval_prompts_from_transcripts(
        agent_prompt, transcripts, user_demographic_info=user_demographic_info
    )


def generate_eval_prompts_from_descriptions(
    agent_prompt: str,
    descriptions: List[str],
    user_demographic_info: Optional[str] = None,
):
    eval_prompts = []
    for description in descriptions:
        part = get_prompt_part(1)
        instruction = (
            f"Generate {part} according to this description: {description}"  # noqa E501
        )
        eval_prompts.extend(
            generate_eval_prompts(agent_prompt, instruction, 1, user_demographic_info)
        )
    return eval_prompts


class EvalGenerator:
    def __init__(self, prompt, user_demographic_info: Optional[str] = None):
        self.prompt = prompt
        self.user_demographic_info = user_demographic_info
        self.transcripts = []
        self.recordings = []
        self.versions = []
        self.version_cases_per_path = 1
        self.projects = []
        self.project_cases_per_path = 1
        self.descriptions = []
        self.edge_cases_count = 0
        self.eval_prompts = []

    def add_from_transcripts(self, transcripts: List[str]):
        self.transcripts.extend(transcripts)
        return self

    def add_from_recordings(self, recording_paths: List[str]):
        self.recordings.extend(recording_paths)
        return self

    def add_from_version(self, version: "Version", cases_per_path=1):
        self.versions.append(version)
        self.version_cases_per_path = cases_per_path
        return self

    def add_from_project(self, project: "Project", cases_per_path=1):
        self.projects.append(project)
        self.project_cases_per_path = cases_per_path
        return self

    def add_from_descriptions(self, descriptions: List[str]):
        self.descriptions.extend(descriptions)
        return self

    def add_edge_cases(self, count: int):
        self.edge_cases_count += count
        return self

    def generate(self):
        if self.eval_prompts:
            raise ValueError(
                "Eval prompts have already been generated. You can access them using .eval_prompts"
            )

        eval_prompts = []
        if self.transcripts:
            eval_prompts.extend(
                generate_eval_prompts_from_transcripts(
                    self.prompt,
                    self.transcripts,
                    user_demographic_info=self.user_demographic_info,
                )
            )

        if self.recordings:
            eval_prompts.extend(
                generate_eval_prompts_from_recording(
                    self.prompt,
                    self.recordings,
                    user_demographic_info=self.user_demographic_info,
                )
            )

        for version in self.versions:
            eval_prompts.extend(
                generate_eval_prompts_from_version(
                    self.prompt,
                    version,
                    self.version_cases_per_path,
                    user_demographic_info=self.user_demographic_info,
                )
            )

        for project in self.projects:
            eval_prompts.extend(
                generate_eval_prompts_from_project(
                    self.prompt,
                    project,
                    self.project_cases_per_path,
                    user_demographic_info=self.user_demographic_info,
                )
            )

        if self.descriptions:
            eval_prompts.extend(
                generate_eval_prompts_from_descriptions(
                    self.prompt,
                    self.descriptions,
                    user_demographic_info=self.user_demographic_info,
                )
            )

        if self.edge_cases_count:
            eval_prompts.extend(
                generate_eval_prompts_for_edge_cases(
                    self.prompt,
                    self.edge_cases_count,
                    user_demographic_info=self.user_demographic_info,
                )
            )

        return eval_prompts
