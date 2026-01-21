import logging
import os
import sys
from typing import Optional

try:
    from rich.logging import RichHandler
    from rich.console import Console
    from rich.syntax import Syntax
    from rich.panel import Panel
except Exception: # If for some reason rich is not available
    RichHandler = None
    Console = None
    Syntax = None
    Panel = None


def _use_colors() -> bool:
    if os.getenv("NO_COLOR"):
        return False
    if not sys.stderr.isatty():
        return False
    return True


def get_logger(name: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        logger.setLevel(level)
        return logger

    if RichHandler and _use_colors():
        handler = RichHandler(rich_tracebacks=True, markup=True)
        formatter = logging.Formatter("%(message)s")
        handler.setFormatter(formatter)
    else:
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%H:%M:%S")
        handler.setFormatter(formatter)

    logger.addHandler(handler)
    logger.propagate = False
    logger.setLevel(level)
    return logger


def pretty_compilation_error(source_path: str, stderr: str) -> None:
    if not (Console and Syntax and Panel):
        print(f"Compilation errors for {source_path}:\n{stderr}")
        return

    console = Console()
    try:
        with open(source_path, "r") as f:
            source = f.read()
    except Exception:
        source = None

    console.rule(f"Compilation failed: {os.path.basename(source_path)}")
    if source:
        syntax = Syntax(source, "cpp", theme="monokai", line_numbers=True)
        console.print(syntax)

    console.print(Panel(stderr.strip(), title="Compiler stderr", style="bold red"))
    console.rule()


def pretty_display_code(source_path: str | None = None, code: str | None = None, language: str = "cpp", title: str | None = None) -> None:
    if not (Console and Syntax and Panel):
        if source_path:
            try:
                with open(source_path, "r") as f:
                    print(f.read())
            except Exception:
                print(code or "")
        else:
            print(code or "")
        return

    console = Console()
    if source_path:
        try:
            with open(source_path, "r") as f:
                code = f.read()
        except Exception:
            code = code or ""

    title = title or (os.path.basename(source_path) if source_path else "Code")
    syntax = Syntax(code or "", language, theme="monokai", line_numbers=True)
    console.print(Panel(syntax, title=title, expand=True))


def pretty_print_message(title: str, message: str) -> None:
    if not Console:
        print(f"{title}:\n{message}")
        return

    console = Console()
    console.print(Panel(message, title=title))
