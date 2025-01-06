import pytest

import mixedvoices as mv


def empty_project(empty_project):
    project = empty_project
    assert "v1" in project.version_ids

    with pytest.raises(ValueError):
        mv.create_project("empty_project", [])

    project = mv.load_project("empty_project")
    assert "v1" in project.version_ids

    with pytest.raises(ValueError):
        mv.load_project("test_nonexistent_project")

    project.load_version("v1")

    with pytest.raises(ValueError):
        project.load_version("v2")

    with pytest.raises(ValueError):
        project.create_version("v1", prompt="Testing prompt")
