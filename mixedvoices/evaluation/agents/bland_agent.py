import requests

from mixedvoices.evaluation.agents.base_agent import BaseAgent


class BlandAgent(BaseAgent):
    def __init__(self, auth_token, pathway_id, start_node_id):
        self.base_url = "https://us.api.bland.ai/v1"
        self.headers = {"authorization": auth_token, "Content-Type": "application/json"}
        self.pathway_id = pathway_id
        self.start_node_id = start_node_id
        self.chat_id = self._create_chat()

    def respond(self, input_text: str):
        # NOTE: Bland agents can't end calls through API, EvalAgent must always hangup
        json = {"message": input_text} if input_text else None
        try:
            response = requests.post(
                self.chat_with_pathway_endpoint(), json=json, headers=self.headers
            ).json()
            return response["data"]["assistant_response"], False
        except Exception as e:
            raise Exception(f"Error in Bland agent's response: {str(e)}") from e

    def create_pathway_chat_endpoint(self):
        return f"{self.base_url}/pathway/chat/create"

    def chat_with_pathway_endpoint(self):
        return f"{self.base_url}/pathway/chat/{self.chat_id}"

    def _create_chat(self):
        json = {
            "pathway_id": self.pathway_id,
            "start_node_id": self.start_node_id,
        }
        try:
            response = requests.post(
                self.create_pathway_chat_endpoint(), json=json, headers=self.headers
            ).json()
            return response["data"]["chat_id"]
        except Exception as e:
            raise Exception(f"Failed to start chat with Bland Agent: {str(e)}") from e
