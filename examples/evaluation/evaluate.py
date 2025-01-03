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


hangup_metric = Metric(
    name="call hangup",
    definition="FAILS if the bot faces problems in ending the call",
    scoring="binary",
)

project = mv.create_project("dental_clinic", metrics=[empathy, hangup_metric])
v1 = project.create_version("v1", prompt=AGENT_PROMPT)

eval_prompt_generator = mv.EvalPromptGenerator(AGENT_PROMPT)
eval_prompt_generator.add_from_descriptions(["Young lady who is scared of root canal"])
all_evals = eval_prompt_generator.generate()

evaluator = project.create_evaluator(all_evals, metric_names=["call hangup"])
evaluator.run(v1, MyDentalAgent, agent_starts=False, model="gpt-4o-mini")
