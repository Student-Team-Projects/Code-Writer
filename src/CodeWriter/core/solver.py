from ..utils.config_loader import Config
from ..utils.file_validator import fileValidator
from ..utils.exceptions import SolverException, CompilationError
from ..utils.logger import get_logger, pretty_print_message

from .compiler import Compiler
from .runner import Runner
from .client import Client
from .tester import Tester

from pathlib import Path

import os

BASE_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "../../.."))
logger = get_logger(__name__)

class Solver:

    def __init__(self, path : str):
        self.directory_path = path
        self.client = None
        self.config = Config()

        self.system_path = PROJECT_ROOT + self.config.get("environment", "system_path")
        self.user_task_path = PROJECT_ROOT + self.config.get("environment", "user_task_path")
        self.error_fix_path = PROJECT_ROOT + self.config.get("environment", "error_fix_path")

        self.public_tests_path = path + "/" + self.config.get("path", "public_tests")
        self.tests_secret_path = path + "/" + self.config.get("path", "private_tests")
        self.problem_problem_path = (
            path + "/" + self.config.get("path", "problem_description")
        )
        self.solution_path = path + "/" + self.config.get("path", "source_file")

        # TODO: set some fancy flags here
        self.compiler = Compiler()
        # TODO: set some reasonable timeout here
        self.timeout  = self.config.get("parameters", "timeout")
        self.runner = Runner()
        self.tester = Tester()

        self.prepare_system()
        self.prepare_error_fix()
        self.prepare_user_task()

        self.last_error = None

    def prepare_system(self):
        language = self.config.get("environment", "language")
        compiler = self.config.get("environment", "compiler")
        flags = self.config.get("environment", "flags").split(" ")
        platform = self.config.get("environment", "platform")

        self.system = fileValidator.read_file(self.system_path)

        self.system = self.system.replace("{language}", language)
        self.system = self.system.replace("{compiler}", compiler)
        self.system = self.system.replace("{platform}", platform)
        self.system = self.system.replace("{flags}", flags)

    def prepare_user_task(self):
        task = fileValidator.read_file(self.user_task_path)
        description = fileValidator.read_file(self.problem_problem_path)

        # Description
        task = task.replace("{description}", description)

        # Example Input
        input_path = os.path.join(self.public_tests_path, self.config.get("path", "input_folder"))
        test_inputs = fileValidator.read_files(input_path)

        test_block_inputs = "\n-------------------------\n".join(test_inputs)
        task = task.replace("{example_input}", test_block_inputs)

        # Example Output
        output_path = os.path.join(self.public_tests_path, self.config.get("path", "expected_output_folder"))
        test_outputs = fileValidator.read_files(output_path)

        test_block_outputs = "\n-------------------------\n".join(test_outputs)
        task = task.replace("{example_output}", test_block_outputs)

        self.user_task = task

    def prepare_error_fix(self):
        error_fix = fileValidator.read_file(self.error_fix_pathq)
        self.error_fix = error_fix

    def begin_chat(self):
        if self.client is not None:
            raise SolverException("Conversation has been already started.")

        # TODO: set the argument properly
        self.client = Client(
            base_url= self.config.get("model", "base_url"), system=self.system, model= self.config.get("model", "model")
        )

        # TODO: uncomment it and return the result
        self.last_response = self.client.chat(self.user_task)
        self.last_response = self.last_response.strip("`cpp")
        with open(self.solution_path, "w") as f:
            f.write(self.last_response)

        return self.last_response
    def continue_chat(self):
        if self.client is None:
            raise SolverException("Conversation has not been started")

        message = self.error_fix.format( **self.last_error)
        self.last_response = self.client.chat(message)
        self.last_response = self.last_response.strip("`cpp")
        with open(self.solution_path, "w") as f:
            f.write(self.last_response)
        return self.last_response
    def validate(self, dir: str) -> bool:

        # Compile
        try:
            binary = self.compiler.compile(self.solution_path)
        except CompilationError as e:
            self.last_error =  {
                "failure_type": "CompilationError",
                "error_details": "Failed to compile to binary"
            }
            return False

        # TODO: move these "in", "expected", etc params to config/settings.json
        input_dir = os.path.join(dir, self.config.get("path", "input_folder"))
        expected_dir = os.path.join(dir, self.config.get("path", "expected_output_folder"))
        error_dir = os.path.join(dir, self.config.get("path", "error_folder"))
        output_dir = os.path.join(dir, self.config.get("path", "output_folder"))

        input_files = sorted(os.listdir(input_dir))
        expected_files = sorted(os.listdir(expected_dir))

        files_count = len(input_files)

        # TODO: validate the folder before compilation. Names and everything
        # Create a class to validate it before the Solver class instance is even created
        if len(expected_files) != files_count:
            raise SolverException("Invalid input folder.")

        for filename in input_files:
            # Run
            input_path = os.path.join(input_dir, filename)
            output_path = os.path.join(output_dir, filename)
            error_path = os.path.join(error_dir, filename)

            self.runner.run(binary, input_path, output_path, error_path)

            # Test
            input_path = os.path.join(input_dir, filename)
            expected_path = os.path.join(expected_dir, filename)
            output_path = os.path.join(output_dir, filename)
            error_path = os.path.join(error_dir, filename)

            result = self.tester.compare_files(expected_path, output_path)
            if not result:
                self.last_error = {
                    "failure_type": "Test Case Failure",
                    "input": input,
                    "expected": expected_path,
                    "output": output_path,
                    "error_file": error_path,
                    "error_details": f"Mismatch in file: {filename}",
                }
                
                print(self.last_error)
                return False

        return True

    def validate_public(self) -> bool:
        pretty_print_message("RUNNING","Running public tests...")
        return self.validate(self.public_tests_path)
    
    def validate_secret(self) -> bool:
        pretty_print_message("RUNNING","Running secret tests...")
        return self.validate(self.tests_secret_path)

# if __name__ == "__main__":
#     solver = Solver("")
#     solver.begin_chat()
#
#     print(solver.validate_public())
