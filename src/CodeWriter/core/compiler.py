import subprocess
import shutil
from pathlib import Path
from typing import List, Optional

from ..utils.file_validator import FileValidator
from ..utils.exceptions import CompilationError
from ..utils.config_loader import Config
from ..utils.logger import get_logger, pretty_compilation_error

logger = get_logger(__name__)
MAX_STDERR_LENGTH = 4000


class Compiler:
    def __init__(self):
        self.config = Config()
        self.compiler = self.config.get("environment", "compiler")
        self.default_flags = self.config.get("environment", "flags").split()


        if not shutil.which(self.compiler):
            raise EnvironmentError(f"Compiler {self.compiler} not found.")

    def compile(
        self, source_path: str, output_dir: Optional[str] = None, flags: Optional[List[str]] = None
    ) -> str:
        validator = FileValidator()
        source = validator.validate(source_path)

        binary_path = validator.validate_and_create(
            output_dir, source.parent, source.stem
        )

        # Prepare flags: defaults always apply, extra flags appended, duplicates dropped in order
        flags = list(dict.fromkeys(self.default_flags + (flags or [])))

        # Execute compilation
        cmd = [self.compiler, str(source), "-o", str(binary_path)]
        cmd.extend(flags)

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        except subprocess.CalledProcessError as e:
            # Capture standard error from the compiler (e.g., syntax errors)
            logger.error("Compilation failed for '%s'", source.name)
            pretty_compilation_error(str(source), e.stderr)
            stderr = e.stderr.strip()
            if len(stderr) > MAX_STDERR_LENGTH:
                stderr = stderr[:MAX_STDERR_LENGTH] + "\n... (compiler output truncated)"
            raise CompilationError(f"Compilation failed for '{source.name}':\n{stderr}")
        except FileNotFoundError as e:
            raise CompilationError(f"Compiler '{self.compiler}' not found.")
        except Exception as e:
            raise CompilationError(f"Unknown error occurred\n {e}")

        return str(binary_path)


