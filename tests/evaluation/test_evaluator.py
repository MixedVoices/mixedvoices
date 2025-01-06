import pytest

from mixedvoices.core.project import Project
from mixedvoices.metrics import empathy


def test_evaluator(empty_project: Project):
    with pytest.raises(ValueError):
        empty_project.create_evaluator(["test_case"], [])

    empty_project.add_metrics([empathy])

    with pytest.raises(KeyError):
        evaluator = empty_project.create_evaluator(
            ["test_case"], ["nonexistent_metric"]
        )

    with pytest.raises(ValueError):
        evaluator = empty_project.create_evaluator(["test_case"], [])

    with pytest.raises(ValueError):
        evaluator = empty_project.create_evaluator([], ["empathy"])

    evaluator = empty_project.create_evaluator(["test_case"], ["empathy"])
    loaded_evaluator = empty_project.load_evaluator(evaluator.id)
    assert evaluator.id == loaded_evaluator.id

    for eval in [evaluator, loaded_evaluator]:
        assert eval.project_id == empty_project.id
        assert eval.metric_names == ["empathy"]
        assert eval.test_cases == ["test_case"]
        assert eval.info["num_eval_runs"] == 0
        assert eval.info["num_prompts"] == 1
        assert eval.info["metric_names"] == ["empathy"]
        assert eval.list_eval_runs() == []
