from typing import List, Dict, Optional
import requests
import json
from ..utils.prompt import Prompt
from ..utils.logger import get_logger, pretty_display_code

try:
    import google.genai as genai
except ImportError:
    genai = None

logger = get_logger(__name__)

class Client:
    def __init__(self, base_url: str, system: str, model: str, provider: str = "ollama", api_key: Optional[str] = None, stream: bool = False):
        self.base_url = base_url
        self.provider = provider.lower()
        self.api_key = api_key
        self.system = system
        self.model_name = model
        self.prompt = Prompt(system, model, stream=False)
        
        if self.provider not in ("ollama", "gemini"):
            raise ValueError(f"Unsupported provider: {self.provider}. Choose 'ollama' or 'gemini'.")
        
        if self.provider == "gemini":
            if not api_key:
                logger.warning("Gemini provider selected but no API key provided. Set 'api_key' in settings.json.")
            elif not genai:
                logger.warning("google-genai package not installed. Install it with: pip install google-genai")
            # API key is passed directly to Client() when needed, no global configure needed

    def chat(self, message: str):
        self.prompt.register_user_message(message)
        payload = self.prompt.get_payload()
        logger.debug("Payload: %s", json.dumps(payload, indent=2))

        try:
            if self.provider == "ollama":
                return self._chat_ollama(payload)
            elif self.provider == "gemini":
                return self._chat_gemini(payload)
        except requests.exceptions.RequestException as e:
            logger.error("Request failed: %s", e, exc_info=True)
        except Exception as e:
            logger.exception("Unexpected error while chatting: %s", e)

    def _chat_ollama(self, payload: Dict) -> str:
        """Chat with Ollama provider via local HTTP API."""
        logger.info(f"→ POST {self.base_url}/api/chat (Ollama)")
        response = requests.post(f"{self.base_url}/api/chat", json=payload)
        response.raise_for_status()

        result = response.json()
        result_text = result.get("message").get("content")

        self.prompt.register_assistant_message(result_text)
        logger.info("Here is your generated code:")
        pretty_display_code(code=result_text, language="cpp", title="Generated Code")

        return result_text

    def _chat_gemini(self, payload: Dict) -> str:
        """Chat with Google Gemini API using the new google-genai SDK."""
        if not genai:
            raise RuntimeError("google-genai package is required for Gemini support. Install with: pip install google-genai")
        
        if not self.api_key:
            raise ValueError("Gemini API key is required. Set it in settings.json under 'model.api_key'.")

        logger.info(f"→ Gemini {self.model_name}")
        
        try:
            # Use the new google.genai API to create a client and send the message
            client = genai.Client(api_key=self.api_key)
            
            # Extract the user message from the payload
            user_message = payload.get("messages", [{}])[-1].get("content", "")
            
            # Send message with system instruction context
            full_message = f"{self.system}\n\n{user_message}" if self.system else user_message
            
            response = client.models.generate_content(
                model=self.model_name,
                contents=full_message
            )
            result_text = response.text

            self.prompt.register_assistant_message(result_text)
            logger.info("Here is your generated code:")
            pretty_display_code(code=result_text, language="cpp", title="Generated Code")

            return result_text
        except Exception as e:
            logger.error("Gemini API error: %s", str(e), exc_info=True)
            raise



