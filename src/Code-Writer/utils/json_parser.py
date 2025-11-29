import json
from exceptions import InvalidJSONException

class JSON_parser:
    @staticmethod
    def validate_json(text, error_message: str = 'Failed to parse JSON object'):
        try:
            json_str = json.dumps(text)
            return json_str
        except (TypeError, OverflowError):
            raise InvalidJSONException(error_message)
    
    @staticmethod
    def parse_json(json_content: str):
        try:
            return json.loads(json_content)
        except json.JSONDecodeError as e:
            raise InvalidJSONException(f"JSON Syntax Error: {str(e)}")
        except TypeError:
            raise InvalidJSONException("Input must be a string, not a file object.")