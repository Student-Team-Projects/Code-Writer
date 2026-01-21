import os
from .exceptions import ConfigurationException, InvalidJSONException
from .json_parser import JSON_Parser
from .logger import get_logger

logger = get_logger(__name__)

BASE_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "../../.."))
SETTINGS_PATH = os.path.join(PROJECT_ROOT, "config", "settings.json")

class Config:
    _instance = None
    _settings = None
    _active_profile = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance.load_settings()
        return cls._instance

    def load_settings(self, path=SETTINGS_PATH):
        if not os.path.exists(path):
            raise ConfigurationException(f"Settings file not found at: {path}")

        try:
            with open(path, "r") as file:
                settings = JSON_Parser.parse_json(file.read())
        except InvalidJSONException:
            raise ConfigurationException("Failed to parse settings.json")

        # Check for profile override via environment variable
        active_profile = os.getenv("CODEWRITER_PROFILE") or settings.get("active_profile", "default")
        profiles_dir = settings.get("profiles_dir", "config/profiles")
        profile_path = os.path.join(PROJECT_ROOT, profiles_dir, f"{active_profile}.json")

        if not os.path.exists(profile_path):
            raise ConfigurationException(
                f"Profile '{active_profile}' not found at: {profile_path}. "
                f"Available profiles: {self._list_profiles(os.path.join(PROJECT_ROOT, profiles_dir))}"
            )

        try:
            with open(profile_path, "r") as file:
                profile_settings = JSON_Parser.parse_json(file.read())
        except InvalidJSONException:
            raise ConfigurationException(f"Failed to parse profile: {profile_path}")

        self._settings = profile_settings
        self._active_profile = active_profile
        logger.debug(f"Loaded config profile: {active_profile} from {profile_path}")

    def _list_profiles(self, profiles_dir: str) -> list:
        """List all available profiles in the profiles directory."""
        if not os.path.exists(profiles_dir):
            return []
        return [f[:-5] for f in os.listdir(profiles_dir) if f.endswith(".json")]

    def get_active_profile(self) -> str:
        """Get the name of the currently active profile."""
        if self._settings is None:
            self.load_settings()
        return self._active_profile

    def get(self, section, key=None):
        if self._settings is None:
            self.load_settings()

        try:
            data = self._settings.get(section)
            if key:
                return data.get(key)
            return data
        except AttributeError:
            raise ConfigurationException(f"Section {section} missing in settings")

config = Config()
