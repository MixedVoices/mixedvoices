from typing import Tuple

from agent import AGENT_PROMPT, DentalAgent, check_conversation_ended

import mixedvoices as mv
from mixedvoices.metrics import Metric, empathy


class MyDentalAgent(mv.BaseAgent):
    def __init__(self, model):
        self.agent = DentalAgent(model=model)

    def respond(self, input_text: str) -> Tuple[str, bool]:
        response = self.agent.get_response(input_text)
        has_conversation_ended = check_conversation_ended(response)
        return response, has_conversation_ended


descriptions = ["Young lady who is scared of coming for root canal"]

project = mv.create_project("dental_clinic")
version = project.create_version("v1", prompt=AGENT_PROMPT)

eval_generator = mv.EvalGenerator(AGENT_PROMPT)
eval_generator.add_from_descriptions(descriptions).add_edge_cases(2)
all_evals = eval_generator.generate()

repetition = Metric(
    name="Repetition",
    definition="If the user has to repeat something or gets frustrated because bot misunderstood",
    scoring="binary",
)

metrics = [empathy, repetition]

evaluator = project.create_evaluator(all_evals, metrics=metrics)
evaluator.run(version, MyDentalAgent, agent_starts=False, model="gpt-4o-mini")
