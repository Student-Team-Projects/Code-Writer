from ..utils.file_validator import FileValidator
from ..utils.logger import get_logger, pretty_print_message

logger = get_logger(__name__)
MAX_SNIPPET_LENGTH = 1000


class Tester:
    def compare_files(self, expected: str, result) -> bool:
        validator = FileValidator()

        expected_file = validator.validate(expected)
        result_file = validator.validate(result)

        with open(expected_file, "r", encoding="utf-8") as f_exp, open(
            result_file, "r", encoding="utf-8"
        ) as f_res:
            content_expected = f_exp.read()
            content_result = f_res.read()

            normalized_expected = " ".join(content_expected.split())
            normalized_result = " ".join(content_result.split())
            ok = normalized_expected == normalized_result
            if ok:
                logger.info("Test passed: %s", expected_file.name)
            else:
                logger.warning("Test failed: %s", expected_file.name)
                expected_snip = content_expected[:MAX_SNIPPET_LENGTH]
                result_snip = content_result[:MAX_SNIPPET_LENGTH]
                pretty_print_message("Expected (snippet)", expected_snip)
                pretty_print_message("Result (snippet)", result_snip)
            return ok
