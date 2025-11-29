from ..utils.file_validator import FileValidator


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

            return normalized_expected == normalized_result
