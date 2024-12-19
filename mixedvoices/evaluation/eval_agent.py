from datetime import datetime

from openai import OpenAI

from mixedvoices.evaluation.utils import history_to_transcript
from mixedvoices.processors.llm_metrics import get_llm_metrics

client = OpenAI()


class EvalAgent:
    def __init__(self, version, prompt, metrics, model="gpt-4o"):
        self.version = version
        self.prompt = prompt
        self.metrics = metrics
        self.model = model
        self.history = []
        self.end = False

    def respond(self, input, end=False):
        if input:
            self.history.append({"role": "user", "content": input})
        if end:
            self.end = True
            transcript = history_to_transcript(self.history)
            scores = get_llm_metrics(transcript, self.version.prompt, **self.metrics)
            self.version.analytics.append(
                {"transcript": transcript, "scores": scores, "prompt": self.prompt}
            )
        messages = [
            {
                "role": "system",
                "content": f"{self.prompt}\nCurrent date and time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}. You will start by greeting. Keep your response short, under 20 words.",  # TODO: this is local time on server
            }
        ]

        messages.extend(self.history)

        try:
            response = client.chat.completions.create(
                model=self.model, messages=messages
            )
            assistant_response = response.choices[0].message.content
            self.history.append({"role": "assistant", "content": assistant_response})
            return assistant_response
        except Exception as e:
            print(f"Error calling OpenAI API: {str(e)}")
            return None
