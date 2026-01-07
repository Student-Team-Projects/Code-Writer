import subprocess
import shutil
from pathlib import Path
from typing import List, Optional

from ..utils.file_validator import FileValidator
from ..utils.exceptions import CompilationError
from ..utils.config_loader import Config

class Compiler:
    def __init__(self):
        self.config = Config()
        self.compiler = self.config.get("environment", "compiler")
        self.default_flags = self.config.get("environment", "flags").split(" ")


        if not shutil.which(self.compiler):
            raise EnvironmentError(f"Compiler {self.compiler} not found.")

    def compile(
        self, source_path: str, output_dir: Optional[str] = None, flags: List[str] = []
    ) -> str:
        validator = FileValidator()
        source = validator.validate(source_path)

        binary_path = validator.validate_and_create(
            output_dir, source.parent, source.stem
        )

        # Prepare flags
        if flags:
            flags = self.default_flags + flags
            flags_set = set(flags)
            flags = list(flags_set)  # unique

        # Execute compilation
        cmd = [self.compiler, str(source), "-o", str(binary_path)]
        cmd.extend(flags)

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        except subprocess.CalledProcessError as e:
            # Capture standard error from the compiler (e.g., syntax errors)
            raise CompilationError(
                f"Compilation failed for '{source.name}':\n{e.stderr}"
            )
        except FileNotFoundError as e:
            raise CompilationError(f"Compiler '{self.compiler}' not found.")
        except Exception as e:
            raise CompilationError(f"Unknown error occurred\n {{e.stderr}}")

        return str(binary_path)


# if __name__ == "__main__":
#     builder = Compiler(compiler="g++", default_flags=["-O2"])
#     # Compile the file
#     try:
#         print("Compiling...")
#         binary_location = builder.compile("hello.cpp")

#         print(f"Success! Binary created at: {binary_location}")

#         # # Run the resulting binary to prove it works
#         # print("\n--- Running Binary ---")
#         # subprocess.run([binary_location])

#     except CompilationError as e:
#         print(f"Error: {e}")
#     except Exception as e:
#         print(f"Unexpected error: {e}")
