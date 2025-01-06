import tempfile
from typing import TYPE_CHECKING, List, Literal, Optional

from tqdm import tqdm

from mixedvoices import models
from mixedvoices.core.utils import get_transcript_and_duration
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


def generate_test_cases(
    agent_prompt: str,
    generation_instruction: str,
    count: int,
    user_demographic_info: Optional[str] = None,
):
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
        model=models.TEST_CASE_GENERATOR_MODEL,
        messages=messages,
    )
    response_text = completion.choices[0].message.content
    prompts = response_text.split("----")
    prompts = [p.strip() for p in prompts if len(p.strip()) > 50]
    assert len(prompts) == count  # TODO: Add retries
    return prompts


# TODO: Use this in future
# def generate_test_cases_for_failure_reasons(
#     agent_prompt: str,
#     failure_reasons: List[str],
#     count: int = 2,
#     user_demographic_info: Optional[str] = None,
# ):
#     test_cases = []
#     for failure_reason in failure_reasons:
#         part = get_prompt_part(count)
#         instruction = (
#             f"Generate {part} that try to recreate this failure: {failure_reason}"
#         )
#         test_cases.extend(
#             generate_test_cases(agent_prompt, instruction, count, user_demographic_info)
#         )
#     return test_cases


def generate_test_cases_from_paths(
    agent_prompt: str,
    paths: List[str],
    count_per_path=2,
    user_demographic_info: Optional[str] = None,
    progress=None,
):
    test_cases = []
    progress.set_postfix({"progress": f"0/{len(paths)} paths processed"})
    for idx, path in enumerate(paths, 1):
        part = get_prompt_part(count_per_path)
        instruction = f"Generate {part} that follow this path: {path}"
        test_cases.extend(
            generate_test_cases(
                agent_prompt, instruction, count_per_path, user_demographic_info
            )
        )
        if progress:
            progress.set_postfix({"progress": f"{idx}/{len(paths)} paths processed"})
            progress.update(count_per_path)
    return test_cases


def generate_test_cases_for_edge_cases(
    agent_prompt: str,
    count: int = 2,
    user_demographic_info: Optional[str] = None,
    progress=None,
):
    if progress:
        progress.set_description("Generating Edge Cases")
        progress.set_postfix({"progress": f"0/{count} cases processed"})

    part = get_prompt_part(count)
    instruction = f"Generate {part} that simulate tricky edge cases."
    result = generate_test_cases(
        agent_prompt, instruction, count, user_demographic_info
    )
    if progress:
        progress.set_postfix({"progress": f"{count}/{count} cases processed"})
        progress.update(count)
    return result


def generate_test_cases_from_transcripts(
    agent_prompt: str,
    transcripts: List[str],
    count: int = 1,
    user_demographic_info: Optional[str] = None,
    progress=None,
):
    if progress:
        progress.set_description("Generating from Transcripts")
        progress.set_postfix(
            {"progress": f"0/{len(transcripts)} transcripts processed"}
        )

    test_cases = []
    for idx, transcript in enumerate(transcripts, 1):
        part = get_prompt_part(count)
        instruction = f"Generate {part} that try to recreate this transcript: {transcript}. You will simulate the USER."
        test_cases.extend(
            generate_test_cases(agent_prompt, instruction, count, user_demographic_info)
        )
        if progress:
            progress.set_postfix(
                {"progress": f"{idx}/{len(transcripts)} transcripts processed"}
            )
            progress.update(count)
    return test_cases


def generate_test_cases_from_recordings(
    agent_prompt: str,
    recording_paths: List[str],
    user_channels: List[str],
    user_demographic_info: Optional[str] = None,
    progress=None,
):
    if progress:
        progress.set_description("Processing Recordings")
        progress.set_postfix(
            {"progress": f"0/{len(recording_paths)} recordings processed"}
        )

    transcripts = []
    with tempfile.TemporaryDirectory() as temp_dir:
        for idx, (path, user_channel) in enumerate(
            zip(recording_paths, user_channels), 1
        ):
            out = get_transcript_and_duration(path, temp_dir, user_channel)
            transcripts.append(out[0])
            if progress:
                progress.set_postfix(
                    {"progress": f"{idx}/{len(recording_paths)} recordings processed"}
                )

    return generate_test_cases_from_transcripts(
        agent_prompt,
        transcripts,
        user_demographic_info=user_demographic_info,
        progress=progress,
    )


def generate_test_cases_from_descriptions(
    agent_prompt: str,
    descriptions: List[str],
    user_demographic_info: Optional[str] = None,
    progress=None,
):
    if progress:
        progress.set_description("Generating from Descriptions")
        progress.set_postfix(
            {"progress": f"0/{len(descriptions)} descriptions processed"}
        )

    test_cases = []
    for idx, description in enumerate(descriptions, 1):
        part = get_prompt_part(1)
        instruction = f"Generate {part} according to this description: {description}"
        test_cases.extend(
            generate_test_cases(agent_prompt, instruction, 1, user_demographic_info)
        )
        if progress:
            progress.set_postfix(
                {"progress": f"{idx}/{len(descriptions)} descriptions processed"}
            )
            progress.update(1)
    return test_cases


class TestCaseGenerator:
    """Generate test cases for evaluation based on the prompt and user demographic info

    Args:
        prompt (str): The prompt of the agent to generate test for
        user_demographic_info (Optional[str]): The user demographic info. Include things like age group, country, accents etc
    """

    def __init__(self, prompt: str, user_demographic_info: Optional[str] = None):
        self.prompt = prompt
        self.user_demographic_info = user_demographic_info
        self.transcripts: List[str] = []
        self.recordings: List[str] = []
        self.user_channels: List[str] = []
        self.versions: List["Version"] = []
        self.versions_paths: List[List[str]] = []
        self.version_cases_per_path: List[int] = []
        self.projects: List["Project"] = []
        self.projects_paths: List[List[str]] = []
        self.project_cases_per_path: List[int] = []
        self.descriptions: List[str] = []
        self.edge_cases_count = 0
        self.test_cases = []

    def add_from_transcripts(self, transcripts: List[str]) -> "TestCaseGenerator":
        """Add test cases from transcripts. 1 test case will be generated for each transcript

        Args:
            transcripts (List[str]): List of transcripts. Transcript should have labels for each utterance . Use 'user:', 'bot:' labels"
        """
        self.transcripts.extend(transcripts)
        return self

    def add_from_recordings(
        self,
        recording_paths: List[str],
        user_channel: Literal["left", "right"] = "left",
    ) -> "TestCaseGenerator":
        """Add test cases from recordings. 1 test case will be generated for each recording

        Args:
            recording_paths (List[str]): List of recording paths. Use stereo recordings with user and bot on different channels.
            user_channel (str, optional): Channel of the user in the recording. Can be "left" or "right". Defaults to "left".
        """
        self.recordings.extend(recording_paths)
        self.user_channels.extend([user_channel] * len(recording_paths))
        return self

    def add_from_version(
        self, version: "Version", cases_per_path: int = 1
    ) -> "TestCaseGenerator":
        """Add test cases from a version. 1 test case will be generated for each path in the version

        Args:
            version (Version): Version object
            cases_per_path (int, optional): Number of test cases to generate for each path. Defaults to 1.
        """
        self._check_generation()
        self.versions.append(version)
        self.versions_paths.append(version._get_paths())
        self.version_cases_per_path.append(cases_per_path)
        return self

    def add_from_project(
        self, project: "Project", cases_per_path: int = 1
    ) -> "TestCaseGenerator":
        """Add test cases from a project. 1 test case will be generated for each path in the project

        Args:
            project (Project): Project object
            cases_per_path (int, optional): Number of test cases to generate for each path. Defaults to 1.
        """
        self._check_generation()
        self.projects.append(project)
        self.projects_paths.append(project._get_paths())
        self.project_cases_per_path.append(cases_per_path)
        return self

    def add_from_descriptions(self, descriptions: List[str]) -> "TestCaseGenerator":
        """Add test cases from rough descriptions. 1 test case will be generated for each description

        Args:
            descriptions (List[str]): List of descriptions
        """
        self._check_generation()
        self.descriptions.extend(descriptions)
        return self

    def add_edge_cases(self, count: int) -> "TestCaseGenerator":
        """Create test cases for edge cases where bot might fail or behave unexpectedly

        Args:
            count (int): Number of test cases to add
        """
        self._check_generation()
        self.edge_cases_count += count
        return self

    @property
    def num_cases(self) -> int:
        project_cases = sum(
            len(paths) * c
            for paths, c in zip(self.projects_paths, self.project_cases_per_path)
        )
        version_cases = sum(
            len(paths) * c
            for paths, c in zip(self.versions_paths, self.version_cases_per_path)
        )
        return sum(
            [
                len(self.transcripts),
                len(self.recordings),
                project_cases,
                version_cases,
                self.edge_cases_count,
                len(self.descriptions),
            ]
        )

    def generate(self, show_progress=True):
        """Generate test cases from all the given inputs"""
        self._check_generation("generate")

        num_cases = self.num_cases
        if num_cases == 0:
            raise ValueError(
                "No test cases generated. "
                "Use one or more of these methods before calling generate: "
                "add_from_transcripts, add_from_recordings, add_from_version, "
                "add_from_project, add_from_descriptions, add_edge_cases"
            )

        try:

            if show_progress:
                progress = tqdm(total=num_cases)
                progress.set_description("Generating test cases")
            else:
                progress = None

            test_cases = []

            if self.recordings:
                test_cases.extend(
                    generate_test_cases_from_recordings(
                        self.prompt,
                        self.recordings,
                        self.user_channels,
                        user_demographic_info=self.user_demographic_info,
                        progress=progress,
                    )
                )

            if self.transcripts:
                test_cases.extend(
                    generate_test_cases_from_transcripts(
                        self.prompt,
                        self.transcripts,
                        user_demographic_info=self.user_demographic_info,
                        progress=progress,
                    )
                )

            if self.descriptions:
                test_cases.extend(
                    generate_test_cases_from_descriptions(
                        self.prompt,
                        self.descriptions,
                        user_demographic_info=self.user_demographic_info,
                        progress=progress,
                    )
                )

            if self.edge_cases_count:
                test_cases.extend(
                    generate_test_cases_for_edge_cases(
                        self.prompt,
                        self.edge_cases_count,
                        user_demographic_info=self.user_demographic_info,
                        progress=progress,
                    )
                )

            for version, version_paths, cases_per_path in zip(
                self.versions, self.versions_paths, self.version_cases_per_path
            ):
                progress.set_description(
                    f"Generating from {version.project_id}/{version.id}'s paths"
                )
                test_cases.extend(
                    generate_test_cases_from_paths(
                        self.prompt,
                        version_paths,
                        cases_per_path,
                        user_demographic_info=self.user_demographic_info,
                        progress=progress,
                    )
                )

            for project, project_paths, cases_per_path in zip(
                self.projects, self.projects_paths, self.project_cases_per_path
            ):
                progress.set_description(f"Generating from {project.id}'s paths")
                test_cases.extend(
                    generate_test_cases_from_paths(
                        self.prompt,
                        project_paths,
                        cases_per_path,
                        user_demographic_info=self.user_demographic_info,
                        progress=progress,
                    )
                )

            self.test_cases = test_cases
            return test_cases
        finally:
            if show_progress:
                progress.close()

    def _check_generation(self, operation="add"):
        if self.test_cases:
            raise ValueError(
                f"Can not {operation}. Test cases have already been generated. "
                "You can access them using .test_cases. "
                "Use a new TestCaseGenerator object to generate more test cases."
            )
