from datetime import datetime
from typing import List

from openai import OpenAI

from enterprise.db_manager import DatabaseManager
from enterprise.metric_analysis import analyze_conversation

client = OpenAI()


class EvalAgent:
    def __init__(self, prompt_run_id, model="gpt-4o"):
        self.db = DatabaseManager()
        self.prompt_run_id = prompt_run_id
        run_details = self.db.get_run_details(prompt_run_id)
        self.prompt = run_details["prompt"]
        self.metadata = run_details["metadata"]
        self.model = model

    def respond(self, input, end):
        db = DatabaseManager()
        history: List[dict] = self.metadata["history"]
        history.append({"role": "user", "content": input})
        if end:
            self.metadata["end"] = True
            db.update_prompt_run(self.prompt_run_id, metadata=self.metadata)
            scores = analyze_conversation(self.prompt_run_id)
            db.update_prompt_run(self.prompt_run_id, metric_scores=scores)
            return

        messages = [
            {
                "role": "system",
                "content": f"{self.prompt}\nCurrent date and time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",  # TODO: this is local time on server
            }
        ]

        messages.extend(self.history)

        try:
            response = client.chat.completions.create(
                model=self.model, messages=messages
            )
            assistant_response = response.choices[0].message.content
            history.append({"role": "assistant", "content": assistant_response})
            db.update_prompt_run(self.prompt_run_id, metadata=self.metadata)
            return assistant_response
        except Exception as e:
            print(f"Error calling OpenAI API: {str(e)}")
            return None


def get_eval_agent(prompt_run_id):
    db = DatabaseManager()
    run_details = db.get_run_details(prompt_run_id)
    prompt = run_details["prompt"]
    metadata = run_details["metadata"]
    return EvalAgent(prompt, metadata)
