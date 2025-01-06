from unittest.mock import patch

from conftest import needs_deepgram_key
from mixedvoices import TestCaseGenerator


@needs_deepgram_key
@patch("mixedvoices.models.TRANSCRIPTION_MODEL", "deepgram/nova-2")
def test_test_case_generator(sample_project, mock_generate_test_cases):
    generator = TestCaseGenerator("prompt")

    generator.add_from_transcripts(["transcript1", "transcript2"])

    assert generator.num_cases == 2

    generator.add_edge_cases(3)

    assert generator.num_cases == 5

    generator.add_from_descriptions(["desc1", "desc2"])

    assert generator.num_cases == 7

    sample_version = sample_project.load_version("v1")
    generator.add_from_version(sample_version)

    assert generator.num_cases == 9

    generator.add_from_project(sample_project)

    assert generator.num_cases == 11

    generator.add_from_recordings(["tests/assets/call2.wav"])

    assert generator.num_cases == 12

    result = generator.generate()

    assert len(result) == 12
