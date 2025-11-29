from pathlib import Path
from typing import Optional, List

import os, stat

from .exceptions import ExecutionError


class FileValidator:
    def validate(self, file_path: str, executable: bool = False) -> Path:
        file = Path(file_path).resolve()

        if not file.exists():
            raise ExecutionError(f'File not found at: {file}')

        if executable:
            if not os.access(str(file), os.X_OK):
                try:
                    current_mode = os.stat(file).st_mode
                    os.chmod(file, current_mode | stat.S_IEXEC)
                except:
                    raise PermissionError(f"File is not executable: {file}")

        return file

    def validate_and_create(
        self, file_path: Optional[str], directory: Path, name: str
    ) -> Path:
        if file_path:
            file = Path(file_path).resolve()
        else:
            file = directory / name

        file.parent.mkdir(parents=True, exist_ok=True)
        return file

    def read_file(self, file_path) -> str:
        file = self.validate(file_path)

        with open(file, "r") as f:
            read = f.read()
        return read

    def read_files(self, dir_path) -> List[str]:
        files = sorted(os.listdir(dir_path))

        test_inputs = []
        for filename in files:
            full_path = os.path.join(dir_path, filename)

            if not os.path.isfile(full_path):
                continue

            content = fileValidator.read_file(full_path)
            test_inputs.append(content)

        return test_inputs


fileValidator = FileValidator()
