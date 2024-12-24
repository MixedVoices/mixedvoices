import pytest

import mixedvoices as mv


def test_project(empty_project):
    project = empty_project
    assert "v1" in project.versions

    with pytest.raises(ValueError):
        mv.create_project("test_project")

    project = mv.load_project("test_project")
    assert "v1" in project.versions

    with pytest.raises(ValueError):
        mv.load_project("test_nonexistent_project")

    project.load_version("v1")

    with pytest.raises(ValueError):
        project.load_version("v2")

    with pytest.raises(ValueError):
        project.create_version("v1", prompt="Testing prompt")