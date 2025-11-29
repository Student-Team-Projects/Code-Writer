from pathlib import Path
from typing import Optional

import os, stat

from exceptions.execution_error import ExecutionError


class FileValidator:
    def validate(self, file_path: str, executable: bool = False) -> Path:
        file = Path(file_path).resolve()

        if not file.exists():
            raise ExecutionError(f"Binary not found at: {file}")

        if executable:
            if not os.access(str(file), os.X_OK):
                try:
                    current_mode = os.stat(file).st_mode
                    os.chmod(file, current_mode | stat.S_IEXEC)
                except:
                    raise PermissionError(f"File is not executable: {file}")

        return file

    def validate_and_create(self, file_path: Optional[str], directory: Path, name: str) -> Path:
        if file_path:
            file = Path(file_path).resolve()
        else:
            file = directory / name

        file.parent.mkdir(parents=True, exist_ok=True)
        return file
