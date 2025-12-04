from typing import List, Dict
import requests
import logging
import json
from ..utils.prompt import Prompt

logging.basicConfig(level=logging.DEBUG)
class Client:
    def __init__(self, base_url: str, system: str, model: str, stream: bool = False)    :
        self.base_url = base_url
        self.prompt = Prompt(system, model,  stream=False)

    def chat(self, message: str):
        self.prompt.register_user_message(message)
        payload = self.prompt.get_payload()
        logging.debug(payload)

        try:
            logging.info(f"Sending request to {self.base_url}...")
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
            print(f"An error occurred: {e}")
        except Exception as e:
            print(f"Unexpected Error Occured: {e}")


# if __name__ == "__main__":
#     client = Client(
#         base_url="https://crucial-ethical-muskrat.ngrok-free.app",
#         system="You are a cat",
#         model="qwen3:14b",
#     )
#
#     client.chat("Tell me a secret")
