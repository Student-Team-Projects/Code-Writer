import os
from .exceptions import ConfigurationException, InvalidJSONException
from .json_parser import JSON_parser


class Config:
    _instance = None
    _settings = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance.load_settings()
        return cls._instance

    def load_settings(self, path="config/settings.json"):
        if not os.path.exists(path):
            raise ConfigurationException(f"Settings file not found at: {path}")

        try:
            with open(path, "r") as file:
                self._settings = JSON_parser.parse_json(file.read())
        except InvalidJSONException:
            raise ConfigurationException("Failed to parse settings.json")

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

if __name__ == "__main__":
    print(config.get('paths'))
