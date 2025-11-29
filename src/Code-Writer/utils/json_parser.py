import json
from exceptions.invalid_json_error import InvalidJSONException

class JSON_parser:
    @staticmethod
    def validate_json(text, error_message: str = 'Failed to parse JSON object'):
        try:
            json_str = json.dumps(text)
            return json_str
        except (TypeError, OverflowError):
            raise InvalidJSONException(error_message)