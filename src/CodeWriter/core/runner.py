from pathlib import Path
import subprocess

from ..utils.file_validator import FileValidator
from ..utils.exceptions import ExecutionError
from ..utils.logger import get_logger, pretty_print_message

logger = get_logger(__name__)


class Runner:
    def __init__(self, timeout: int = 15):
        self.timeout = timeout

    def run(self, binary_path: str, input: str, output: str, error: str):
        validator = FileValidator()

        binary = validator.validate(binary_path, executable=True)
        input_file = validator.validate(input)

        output_file = validator.validate_and_create(
            output, input_file.parent, input_file.stem
        )
        error_file = validator.validate_and_create(
            error, input_file.parent, input_file.stem
        )

        # Construct Command
        cmd = [str(binary)]

        try:
            logger.info("Running: %s (input=%s)", binary, input_file.name)
            with open(input_file, "r") as f_in, open(output_file, "w") as f_out, open(
                error_file, "w"
            ) as f_err:
                result = subprocess.run(
                    cmd,
                    text=True,
                    check=True,
                    timeout=self.timeout,
                    stdin=f_in,
                    stdout=f_out,
                    stderr=f_err,
                )
            logger.debug("Execution finished, output=%s, error=%s", output_file, error_file)

        except subprocess.TimeoutExpired:
            logger.error("Process timed out after %s seconds", self.timeout)
            raise ExecutionError(f"Process timed out after {self.timeout} seconds.")
        except subprocess.CalledProcessError as e:
            try:
                with open(error_file, "r") as ef:
                    stderr = ef.read()
            except Exception:
                stderr = e.stderr or ""

            pretty_print_message("Runtime Error", stderr)
            logger.exception("Runtime Error while running %s", binary)
            raise ExecutionError(f"Runtime Error:\n{stderr}")
        except Exception as e:
            logger.exception("Unknown error while executing %s: %s", binary, e)
            raise ExecutionError(f"Unknown Error occured: {e}")


# if __name__ == "__main__":
#     runner = Runner(timeout=5)

#     print("--- Executing Runner ---")
#     try:
#         # We explicitly define output paths to ensure validate_and_create works
#         runner.run(
#             binary_path="./hello",
#             input="data_in.txt",
#             output="results/final_output.txt",
#             error="logs/error_log.txt",
#         )
#         print("Execution finished successfully.")
#     except Exception as e:
#         print(f"Test Failed with Exception: {e}")
