from pathlib import Path
import subprocess

from utils.file_validator import FileValidator
from utils.exceptions import ExecutionError


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

        except subprocess.TimeoutExpired:
            raise ExecutionError(f"Process timed out after {self.timeout} seconds.")
        except subprocess.CalledProcessError as e:
            raise ExecutionError(f"Runtime Error:\n{e.stderr}")
        except Exception as e:
            raise ExecutionError(f"Unknown Error occured: {e}")


if __name__ == "__main__":
    runner = Runner(timeout=5)

    print("--- Executing Runner ---")
    try:
        # We explicitly define output paths to ensure validate_and_create works
        runner.run(
            binary_path="./hello",
            input="data_in.txt",
            output="results/final_output.txt",
            error="logs/error_log.txt",
        )
        print("Execution finished successfully.")
    except Exception as e:
        print(f"Test Failed with Exception: {e}")
