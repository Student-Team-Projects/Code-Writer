from typing import List, Dict, Optional
import requests
import json
from ..utils.prompt import Prompt
from ..utils.exceptions import SolverException
from ..utils.logger import get_logger, pretty_display_code, pretty_print_message

try:
    import google.genai as genai
except ImportError:
    genai = None

logger = get_logger(__name__)
REQUEST_TIMEOUT = 600  # seconds; local models can take minutes per answer

class Client:
    def __init__(self, base_url: str, system: str, model: str, provider: str = "ollama", api_key: Optional[str] = None, stream: bool = False, num_ctx: int = 12288, think: bool = False, debug: bool = False):
        self.base_url = base_url
        self.provider = provider.lower()
        self.api_key = api_key
        self.system = system
        self.model_name = model
        self.debug = debug
        self.prompt = Prompt(system, model, num_ctx=num_ctx, stream=False, think=think)
        
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
        if self.debug:
            self._print_prompt()

        try:
            if self.provider == "ollama":
                return self._chat_ollama(payload)
            elif self.provider == "gemini":
                return self._chat_gemini(payload)
        except requests.exceptions.RequestException as e:
            raise SolverException(f"Request to {self.provider} failed: {e}") from e

    def _print_prompt(self):
        """Print the system prompt (first request only) and the new user prompt being sent."""
        messages = self.prompt.get_messages()
        if len(messages) == 2:
            pretty_print_message("SYSTEM PROMPT", messages[0]["content"])
        total_chars = sum(len(m["content"]) for m in messages)
        title = f"PROMPT #{len(messages) // 2} → {self.provider} ({len(messages)} messages, {total_chars} chars in conversation)"
        pretty_print_message(title, messages[-1]["content"])

    def _chat_ollama(self, payload: Dict) -> str:
        """Chat with Ollama provider via local HTTP API."""
        logger.info(f"→ POST {self.base_url}/api/chat (Ollama)")
        response = requests.post(f"{self.base_url}/api/chat", json=payload, timeout=REQUEST_TIMEOUT)
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
            
            # Send the whole conversation so fix-up requests keep the task and previous code
            contents = [
                {"role": "model" if m["role"] == "assistant" else "user", "parts": [{"text": m["content"]}]}
                for m in payload.get("messages", [])
                if m["role"] != "system"
            ]

            response = client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config={"system_instruction": self.system} if self.system else None
            )
            result_text = response.text

            self.prompt.register_assistant_message(result_text)
            logger.info("Here is your generated code:")
            pretty_display_code(code=result_text, language="cpp", title="Generated Code")

            return result_text
        except Exception as e:
            raise SolverException(f"Gemini API error: {e}") from e



