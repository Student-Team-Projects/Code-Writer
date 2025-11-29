from typing import List, Dict

from utils.json_parser import JSON_parser


class Prompt:
    def __init__(self, system: str, max_tokens: int = 256, stream: bool = False, model: str = "Llama-4-Maverick-17B-128E-Instruct-FP8"):
        self.model = model # TODO: validate model before setting it up
        self.system = system
        self.messages = []
        self.response_schema = None
        self.max_tokens = max_tokens
        self.stream = stream

    def register_user_message(self, message: str):
        self.messages.append({"role": "user", "content": message})

    def register_assistant_message(self, message: str):
        self.messages.append(
            {self.messages.append({"role": "assistant", "content": message})}
        )

    def get_messages(self) -> List[Dict]:
        system = {"role": "system", "content": self.system}
        return [system] + self.messages

    def set_response_schema(self, response_schema: Dict):
        json_response_schema = JSON_parser.validate_json(
            response_schema, error_message="Invalid response schema"
        )
        self.response_schema = response_schema

    def get_payload(self):
        payload = {
            "model": self.model,
            "messages": self.get_messages(),
            "response_format": self.response_schema,
            "max_tokens": self.max_tokens,
            "stream": self.stream,
        }
        return payload
