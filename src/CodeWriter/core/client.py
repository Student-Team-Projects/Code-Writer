from typing import List, Dict
import requests
import json
from ..utils.prompt import Prompt
from ..utils.logger import get_logger

logger = get_logger(__name__)
class Client:
    def __init__(self, base_url: str, system: str, model: str, stream: bool = False)    :
        self.base_url = base_url
        self.prompt = Prompt(system, model,  stream=False)

    def chat(self, message: str):
        self.prompt.register_user_message(message)
        payload = self.prompt.get_payload()
        logger.debug("Payload: %s", json.dumps(payload, indent=2))

        try:
            logger.info(f"→ POST {self.base_url}/api/chat (CONNECTING TO MODEL)")
            response = requests.post(f"{self.base_url}/api/chat", json=payload)

            response.raise_for_status()

            result = response.json()
            result_text = result.get("message").get("content")

            #print(f"Response: {result_text}")
            # TODO: retrieve text message from result

            self.prompt.register_assistant_message(result_text)

            # TODO: return the generated code
            return result_text

        except requests.exceptions.RequestException as e:
            logger.error("Request failed: %s", e, exc_info=True)
        except Exception as e:
            logger.exception("Unexpected error while chatting: %s", e)


# if __name__ == "__main__":
#     client = Client(
#         base_url="https://crucial-ethical-muskrat.ngrok-free.app",
#         system="You are a cat",
#         model="qwen3:14b",
#     )
#
#     client.chat("Tell me a secret")
