from typing import List, Dict
import requests
import logging

from ..utils.prompt import Prompt


class Client:
    def __init__(self, base_url: str, system: str, model: str, stream: bool = False):
        self.base_url = base_url
        self.prompt = Prompt(system, stream=False)

    def chat(self, message: str):
        self.prompt.register_user_message(message)

        payload = self.prompt.get_payload()
        requests.post(f"{self.base_url}/api/generate", data=payload)

        try:
            logging.info(f"Sending request to {self.base_url}...")
            response = requests.post(f"{self.base_url}/api/generate", data=payload)

            response.raise_for_status()

            result = response.json()
            # TODO: retrieve text message from result
            # self.prompt.register_assistant_message(result)

            # TODO: return the generated code
            return "No reult here yet"

        except requests.exceptions.RequestException as e:
            print(f"An error occurred: {e}")
        except Exception as e:
            print(f"Unexpected Error Occured: {e}")


# if __name__ == "__main__":
#     client = Client(
#         base_url="https://crucial-ethical-muskrat.ngrok-free.app",
#         system="You are a cat",
#         model="llama3",
#     )

#     client.chat("Tell me a secret.")
