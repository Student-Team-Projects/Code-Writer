from typing import List, Dict

from .json_parser import JSON_Parser


class Prompt:
    def __init__(self, system: str,  model: str, max_tokens: int = 2048, stream: bool = False, think: bool = False):
        self.model = model # TODO: validate model before setting it up
        self.system = system
        self.messages = []
        self.response_schema = None
        self.max_tokens = max_tokens
        self.stream = stream
        self.think = think

    def register_user_message(self, message: str):
        self.messages.append({"role": "user", "content": message})

    def register_assistant_message(self, message: str):
        self.messages.append({"role": "assistant", "content": message})

    def get_messages(self) -> List[Dict]:
        system = {"role": "system", "content": self.system}
        return [system] + self.messages

    def set_response_schema(self, response_schema: Dict):
        json_response_schema = JSON_Parser.validate_json(
            response_schema, error_message="Invalid response schema"
        )
        self.response_schema = response_schema

    def get_payload(self):
        payload = {
            "model": self.model,
            "messages": self.get_messages(),
            #"format": self.response_schema,
            # "options.num_ctx": self.max_tokens,
            "stream": self.stream,
            "think" : self.think
        }
        return payload
