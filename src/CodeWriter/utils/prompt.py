from typing import List, Dict

from .json_parser import JSON_Parser


class Prompt:
    def __init__(self, system: str,  model: str, num_ctx: int = 12288, stream: bool = False, think: bool = False):
        self.model = model #
        self.system = system
        self.messages = []
        self.response_schema = None
        self.num_ctx = num_ctx
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
            # Ollama's default context (often 4096) silently drops the start of the conversation
            "options": {"num_ctx": self.num_ctx},
            "stream": self.stream,
            "think" : self.think
        }
        return payload
