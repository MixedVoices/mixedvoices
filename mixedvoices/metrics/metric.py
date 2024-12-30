from dataclasses import dataclass
from typing import Literal

# TODO: add more metrics, define better
# TODO: allow creation of custom call metrics


@dataclass
class Metric:
    name: str
    definition: str
    scoring: Literal["binary", "continuous"]
    include_prompt: bool = False

    def __post_init__(self):
        if self.scoring not in ["binary", "continuous"]:
            raise ValueError("Scoring must be 'binary' or 'continuous'")
        self.name = self.name.lower()

    @property
    def expected_values(self):
        if self.scoring == "binary":
            return ["PASS", "FAIL", "N/A"]
        elif self.scoring == "continuous":
            return list(range(11)) + ["N/A"]

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"Metric(name='{self.name}', definition='{self.definition}', scoring_range={self.scoring}), include_prompt={self.include_prompt})"

    def to_dict(self):
        return {
            "name": self.name,
            "definition": self.definition,
            "scoring": self.scoring,
            "include_prompt": self.include_prompt,
        }
