import os
from .exceptions import ConfigurationException, InvalidJSONException
from .json_parser import JSON_Parser
from .logger import get_logger

logger = get_logger(__name__)

BASE_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "../../.."))
SETTINGS_PATH = os.path.join(PROJECT_ROOT, "config", "settings.json")
EXAMPLE_PATH = os.path.join(PROJECT_ROOT, "codewriter.example.json")

# Name of the user's config file, looked up in the current directory when --config is not given
CONFIG_FILENAME = "codewriter.json"

PROVIDER_NAMES = {
    "ollama": "Ollama",
    "gemini": "Gemini",
    "openai": "OpenAI",
    "mistral": "Mistral",
    "deepseek": "DeepSeek",
}
PROVIDERS = tuple(PROVIDER_NAMES)


def _read_json(path: str) -> dict:
    try:
        with open(path, "r") as file:
            data = JSON_Parser.parse_json(file.read())
    except InvalidJSONException:
        raise ConfigurationException(f"Failed to parse JSON in {path}")
    if not isinstance(data, dict):
        raise ConfigurationException(f"{path} must contain a JSON object")
    return data


def _merge(defaults: dict, overrides: dict) -> dict:
    """Return a new dict with overrides merged recursively over defaults."""
    result = dict(defaults)
    for k, v in overrides.items():
        if isinstance(v, dict) and isinstance(result.get(k), dict):
            result[k] = _merge(result[k], v)
        else:
            result[k] = v
    return result


class Config:
    """The run configuration: built-in defaults (config/settings.json) overridden by the user's codewriter.json.

    The file lists one model ("model": {...}) or several ("models": [{...}, ...]); models() returns them.

    Call Config.load(path) once at startup; afterwards Config() returns the loaded configuration.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            raise ConfigurationException("Configuration not loaded; call Config.load() first")
        return cls._instance

    @classmethod
    def load(cls, path: str = None) -> "Config":
        path = os.path.abspath(path or CONFIG_FILENAME)
        if not os.path.isfile(path):
            raise ConfigurationException(
                f"Config file not found: {path}\n"
                f"Create one from the example: cp {EXAMPLE_PATH} {CONFIG_FILENAME}"
            )
        if not os.path.isfile(SETTINGS_PATH):
            raise ConfigurationException(f"Built-in defaults not found at: {SETTINGS_PATH}")

        defaults = _read_json(SETTINGS_PATH)
        user = _read_json(path)
        settings = _merge(defaults, user)
        cls._validate(settings, path)

        instance = super().__new__(cls)
        instance._settings = settings
        instance.path = path
        cls._instance = instance
        logger.debug(f"Loaded config from {path}")
        return instance

    @staticmethod
    def _validate(settings: dict, path: str):
        """Normalize the model list into settings["models"] and check every entry."""
        if "models" in settings and "model" in settings:
            raise ConfigurationException(f"{path}: use either \"model\" (one model) or \"models\" (a list), not both")
        if "models" in settings:
            models = settings["models"]
            if not isinstance(models, list) or not models:
                raise ConfigurationException(f"{path}: \"models\" must be a non-empty list")
        elif isinstance(settings.get("model"), dict):
            models = [settings.pop("model")]
        else:
            raise ConfigurationException(f"{path}: missing \"model\" (one model) or \"models\" (a list)")

        global_params = settings.get("parameters", {})
        names = set()
        normalized = []
        for i, entry in enumerate(models):
            where = f"{path}: models[{i}]" if "models" in settings else f"{path}: model"
            if not isinstance(entry, dict):
                raise ConfigurationException(f"{where} must be an object")
            model = dict(entry)

            provider = str(model.get("provider") or "").lower()
            if provider not in PROVIDERS:
                raise ConfigurationException(
                    f"{where}.provider must be one of {', '.join(PROVIDERS)} (got {model.get('provider')!r})"
                )
            model["provider"] = provider

            if not model.get("model"):
                raise ConfigurationException(f"{where}.model is required (e.g. \"qwen3:14b\")")
            if provider == "ollama" and not model.get("base_url"):
                raise ConfigurationException(f"{where}.base_url is required for Ollama (e.g. \"http://localhost:11434\")")
            if provider != "ollama" and not model.get("api_key"):
                raise ConfigurationException(f"{where}.api_key is required for {PROVIDER_NAMES[provider]}")

            name = model.get("name") or model["model"]
            if name in names:
                raise ConfigurationException(f"{where}: duplicate model name {name!r}; give each entry a unique \"name\"")
            names.add(name)
            model["name"] = name

            # Per-model parameters override the global "parameters" section
            own_params = model.get("parameters") or {}
            if not isinstance(own_params, dict):
                raise ConfigurationException(f"{where}.parameters must be an object")
            model["parameters"] = _merge(global_params, own_params)
            attempts = model["parameters"].get("max_attempts")
            if not isinstance(attempts, int) or isinstance(attempts, bool) or attempts < 1:
                raise ConfigurationException(f"{where}: parameters.max_attempts must be a positive integer")

            normalized.append(model)

        settings["models"] = normalized

    def models(self, name: str = None) -> list:
        """All configured models, or only the one called `name`."""
        models = self._settings["models"]
        if name is None:
            return models
        selected = [m for m in models if m["name"] == name]
        if not selected:
            available = ", ".join(m["name"] for m in models)
            raise ConfigurationException(f"No model named {name!r} in {self.path}. Available: {available}")
        return selected

    def get(self, section, key=None):
        data = self._settings.get(section)
        if data is None:
            raise ConfigurationException(f"Section {section} missing in config")
        if key:
            return data.get(key)
        return data
