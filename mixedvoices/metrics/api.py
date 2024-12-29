import json
import os
from typing import Dict, List, Literal, Optional

from mixedvoices import constants
from mixedvoices.metrics.definitions import Metric, get_all_default_metrics

# TODO: add more metrics, define better
# TODO: allow creation of custom call metrics


def serialize_metrics(metrics: list[Metric]):
    return [metric.to_dict() for metric in metrics]


def deserialize_metrics(metrics: list[dict]):
    return [Metric(**metric) for metric in metrics]


# TODO: Check behaviour in tests
class GlobalMetrics:
    def __init__(self, metrics_file: str):
        self._metrics: Dict[str, Metric] = {}
        self._metrics_file = metrics_file
        self.load()

    def add_metric(self, metric: Metric) -> None:
        """
        Add a new metric to the collection.
        Raises ValueError if metric with same name already exists.
        """
        if metric.name in self._metrics:
            raise ValueError(
                f"Metric with name '{metric.name}' already exists. Use list_metrics to view all existing metrics."
            )
        self._metrics[metric.name] = metric
        self.save()

    def update_metric(self, metric: Metric) -> None:
        """
        Update an existing metric.
        Raises ValueError if metric doesn't exist.
        """
        if metric.name not in self._metrics:
            raise ValueError(
                f"Metric with name '{metric.name}' does not exist. Use list_metrics to view all existing metrics."
            )
        self._metrics[metric.name] = metric
        self.save()

    def remove_metric(self, name: str, force: bool = False) -> None:
        """
        Remove a metric by name.
        Raises ValueError if metric doesn't exist.
        """
        name = name.lower()
        if not force:
            raise ValueError(
                "This will delete the metric and any projects using it will no longer be able to use it. Use force=True to continue."
            )
        if name not in self._metrics:
            raise ValueError(f"Metric with name '{name}' does not exist")
        del self._metrics[name]
        self.save()

    def get_metric(self, name: str, raise_key_error: bool = True) -> Optional[Metric]:
        """Get a metric by name."""
        name = name.lower()

        if name not in self._metrics:
            if raise_key_error:
                raise KeyError(
                    f"Metric with name '{name}' does not exist. Used add_metric() to add it or add from dashboard."
                )
            return None
        return self._metrics[name]

    def get_metrics(self, names: List[str]) -> List[Metric]:
        """
        Get multiple metrics by their names.
        Returns only the metrics that exist, skipping any names that aren't found.
        """
        names = [name.lower() for name in names]
        metrics = []
        for name in names:
            if name not in self._metrics:
                raise KeyError(
                    f"Metric with name '{name}' does not exist. Used add_metric() to add it or add from dashboard."
                )
            metrics.append(self._metrics[name])
        return metrics

    def get_all_metrics(self) -> List[Metric]:
        """Get all metrics as a list."""
        return list(self._metrics.values())

    def reset_to_defaults(self, force: bool = False) -> None:
        """Reset metrics to default values."""
        if not force:
            raise ValueError(
                "This will delete all custom metric definitions. Projects using them will no longer analyze them. Use force=True to continue."
            )
        self._metrics = {metric.name: metric for metric in get_all_default_metrics()}
        self.save()

    def load(self) -> None:
        """Load metrics from file."""
        if not os.path.exists(self._metrics_file):
            self._metrics = {
                metric.name: metric for metric in get_all_default_metrics()
            }
            self.save()
            return

        with open(self._metrics_file, "r") as f:
            metrics_data = json.load(f)
            metrics = deserialize_metrics(metrics_data)
            self._metrics = {metric.name: metric for metric in metrics}

    def save(self) -> None:
        """Save metrics to file."""
        with open(self._metrics_file, "w") as f:
            json.dump(serialize_metrics(self.get_all_metrics()), f, indent=4)


# Create a singleton instance with the metrics file
_instance = GlobalMetrics(constants.METRICS_FILE)


# Public interface
def add_metric(
    name: str,
    definition: str,
    scoring: Literal["binary", "continuous"],
    include_prompt: bool = False,
) -> None:
    """Add a new metric."""
    metric = Metric(name, definition, scoring, include_prompt)
    _instance.add_metric(metric)


def update_metric(
    name: str,
    definition: str,
    scoring: Literal["binary", "continuous"],
    include_prompt: bool = False,
) -> None:
    """Update an existing metric."""
    metric = Metric(name, definition, scoring, include_prompt)
    _instance.update_metric(metric)


def remove_metric(name: str, force: bool = False) -> None:
    """Remove a metric by name."""
    _instance.remove_metric(name, force)


def get_metric(name: str) -> Dict:
    """Get a metric by name."""
    return _instance.get_metric(name).to_dict()


def list_metrics() -> List[Dict]:
    """List all metrics with details."""
    metrics = _instance.get_all_metrics()
    return serialize_metrics(metrics)


def reset_metrics(force: bool = False) -> None:
    """Reset metrics to defaults."""
    _instance.reset_to_defaults(force)


def get_metrics(names: List[str]) -> List[Dict]:
    """
    Get multiple metrics by their names.
    """
    metrics = _instance.get_metrics(names)
    return serialize_metrics(metrics)


def list_metric_names() -> List[str]:
    """List all metric names."""
    return [metric.name for metric in _instance.get_all_metrics()]
