from ..utils.config_loader import Config
from ..utils.file_validator import fileValidator
from ..utils.exceptions import ExecutionError, SolverException, CompilationError
from ..utils.logger import get_logger, pretty_print_message

from .compiler import Compiler
from .runner import Runner
from .client import Client
from .tester import Tester

from pathlib import Path

import os
import re

BASE_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "../../.."))
logger = get_logger(__name__)

THINK_BLOCK = re.compile(r"<think>.*?</think>", re.DOTALL)
CODE_BLOCK = re.compile(r"```[\w+-]*\n(.*?)```", re.DOTALL)
STRAY_FENCE = re.compile(r"^```[\w+-]*\n|\n?```\s*$")


def extract_code(response: str) -> str:
    """Return the source code from a model reply, dropping <think> blocks, prose and markdown fences."""
    response = THINK_BLOCK.sub("", response)
    blocks = CODE_BLOCK.findall(response)
    if blocks:
        code = max(blocks, key=len)
    else:
        # No complete fenced block (e.g. reply without markdown, or cut off): drop any stray fence lines
        code = STRAY_FENCE.sub("", response.strip())
    return code.strip() + "\n"

class Solver:

    def __init__(self, path : str, model: dict, debug: bool = False):
        """model: one entry from Config.models() (provider, model, base_url, api_key, parameters)."""
        self.directory_path = path
        self.client = None
        self.config = Config()
        self.model = model
        self.parameters = model["parameters"]
        self.debug = debug

        self.system_path = PROJECT_ROOT + self.config.get("path", "system_path")
        self.user_task_path = PROJECT_ROOT + self.config.get("path", "user_task_path")
        self.error_fix_path = PROJECT_ROOT + self.config.get("path", "error_fix_path")

        self.public_tests_path = path + "/" + self.config.get("path", "public_tests")
        self.tests_secret_path = path + "/" + self.config.get("path", "private_tests")
        self.problem_problem_path = (
            path + "/" + self.config.get("path", "problem_description")
        )
        self.solution_path = path + "/" + self.config.get("path", "source_file")

        self.compiler = Compiler()
        self.max_attempts = self.parameters["max_attempts"]
        self.runner = Runner()
        self.tester = Tester()

        self.prepare_system()
        self.prepare_user_task()

        self.last_error = None

    def prepare_system(self):
        self.system = fileValidator.read_file(self.system_path)

        self.system = self.system.format(**self.config.get("environment"))


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
        error_fix = fileValidator.read_file(self.error_fix_path)
        if self.last_error["secret"]:
            self.last_error["error_details"] = "This test is secret"
        self.error_fix = error_fix.format(**self.last_error)


    def begin_chat(self):
        if self.client is not None:
            raise SolverException("Conversation has been already started.")

        model = self.model
        self.client = Client(
            base_url=model.get("base_url"),
            system=self.system,
            model=model["model"],
            provider=model["provider"],
            api_key=model.get("api_key") or None,
            num_ctx=self.parameters.get("num_ctx") or 12288,
            think=self.parameters.get("think") or False,
            debug=self.debug
        )

        return self.save_solution(self.client.chat(self.user_task))

    def continue_chat(self):
        if self.client is None:
            raise SolverException("Conversation has not been started")

        #prepare error message
        self.prepare_error_fix()
        message = self.error_fix

        return self.save_solution(self.client.chat(message))

    def save_solution(self, response: str) -> str:
        self.last_response = extract_code(response)
        with open(self.solution_path, "w") as f:
            f.write(self.last_response)
        return self.last_response

    def validate(self, dir: str, secret : bool) -> bool:
        # Compile
        try:
            binary = self.compiler.compile(self.solution_path)
        except CompilationError as e:
            self.last_error =  {
                "failure_type": "CompilationError",
                "error_details": "Failed to compile to binary : " + str(e),
                "secret": secret
            } 
            return False


        input_dir = os.path.join(dir, self.config.get("path", "input_folder"))
        expected_dir = os.path.join(dir, self.config.get("path", "expected_output_folder"))
        error_dir = os.path.join(dir, self.config.get("path", "error_folder"))
        output_dir = os.path.join(dir, self.config.get("path", "output_folder"))

        input_files = sorted(os.listdir(input_dir))
        expected_files = sorted(os.listdir(expected_dir))

        files_count = len(input_files)

        if len(expected_files) != files_count:
            raise SolverException("Invalid input folder.")

        for filename in input_files:
            # Run
            input_path = os.path.join(input_dir, filename)
            expected_path = os.path.join(expected_dir, filename)
            output_path = os.path.join(output_dir, filename)
            error_path = os.path.join(error_dir, filename)

            try:
                self.runner.run(binary, input_path, output_path, error_path)
            except ExecutionError as e:
                self.last_error = {"failure_type": "ExecutionError",
                                   "input": input_path,
                                   "output": output_path,
                                   "error_file": error_path,
                                   "secret": secret,
                                   "error_details": (
                                        f" Runtime error: {str(e)}\n While running following test: \n---INPUT---\n" +
                                        fileValidator.read_file(input_path) + "\n---OUTPUT---\n" +
                                        fileValidator.read_file(output_path) + "\n---EXPECTED---\n" +
                                        fileValidator.read_file(expected_path) + "\n---ERROR---\n" +
                                        fileValidator.read_file(error_path) + "\n")}
                return False
            

            result = self.tester.compare_files(expected_path, output_path)
            if not result:
                self.last_error = {"failure_type": "Test Case Failure",
                                   "input": input_path,
                                   "expected": expected_path,
                                   "output": output_path,
                                   "error_file": error_path,
                                   "secret": secret,
                                   "error_details": (
                                            f" Mismatch in following test: \n---INPUT---\n" +
                                            fileValidator.read_file(input_path) + "\n---OUTPUT---\n" +
                                            fileValidator.read_file(output_path) + "\n---EXPECTED---\n" +
                                            fileValidator.read_file(expected_path) + "\n---ERROR---\n" +
                                            fileValidator.read_file(error_path) + "\n")}
                return False

        return True

    def validate_public(self) -> bool:
        pretty_print_message("RUNNING","Running public tests...")
        return self.validate(self.public_tests_path, False)
    
    def validate_secret(self) -> bool:
        if not os.path.isdir(self.tests_secret_path):
            logger.warning("No secret tests found at %s, skipping them", self.tests_secret_path)
            return True
        pretty_print_message("RUNNING","Running secret tests...")
        return self.validate(self.tests_secret_path, True)

