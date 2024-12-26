from typing import Tuple

from agent import DentalAgent, check_conversation_ended

import mixedvoices as mv


class MyDentalAgent(mv.BaseAgent):
    def __init__(self, model):
        self.agent = DentalAgent(model=model)

    def respond(self, input_text: str) -> Tuple[str, bool]:
        response = self.agent.get_response(input_text)
        has_conversation_ended = check_conversation_ended(response)
        return response, has_conversation_ended


project = mv.load_project("dental_clinic")
version = project.load_version("v1")
evaluator = version.create_evaluator(1, 1, 1)
evaluator.run(MyDentalAgent, agent_starts=True, model="gpt-4o-mini")
