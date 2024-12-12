from mixedvoices.evaluation.eval_agent import get_eval_agent


class EvalPromptRun:
    def __init__(self, prompt_run_id):
        self.prompt_run_id = prompt_run_id
        self.is_active = True

    def respond(self, input_text: str, end: bool = False):
        # TODO replace with server call
        eval_agent = get_eval_agent(self.prompt_run_id)
        return eval_agent.respond(input_text, end)
