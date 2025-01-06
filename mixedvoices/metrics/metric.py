from dataclasses import dataclass
from typing import Literal

# TODO: add more metrics, define better
# TODO: allow creation of custom call metrics


@dataclass
class Metric:
    """Define a custom metric.

    Args:
        name (str): The name of the metric.
        definition (str): The definition of the metric.
        scoring (str): The scoring range of the metric. Can be 'binary' or 'continuous'.
            binary for PASS/FAIL, continuous for 0-10 scale
        include_prompt (bool, optional): Whether to include the agent prompt when evaluating the metric.
            Example: To check for hallucination, agent prompt should be included. But for conciseness, it shouldn't. Defaults to False.
    """

    name: str
    "The name of the metric."
    definition: str
    "The definition of the metric."
    scoring: Literal["binary", "continuous"]
    "The scoring range of the metric. Can be 'binary' or 'continuous'."
    include_prompt: bool = False
    "Whether to include the agent prompt when evaluating the metric."

    def __post_init__(self):
        if self.scoring not in ["binary", "continuous"]:
            raise ValueError("Scoring must be 'binary' or 'continuous'")
        self.name = self.name.lower()

    @property
    def expected_values(self):
        """Returns the expected values for the metric based on the scoring type."""
        if self.scoring == "binary":
            return ["PASS", "FAIL", "N/A"]
        elif self.scoring == "continuous":
            return list(range(11)) + ["N/A"]

    def to_dict(self):
        """Returns a dictionary representation of the metric."""
        return {
            "name": self.name,
            "definition": self.definition,
            "scoring": self.scoring,
            "include_prompt": self.include_prompt,
        }

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"Metric(name='{self.name}', definition='{self.definition}', scoring_range={self.scoring}), include_prompt={self.include_prompt})"
