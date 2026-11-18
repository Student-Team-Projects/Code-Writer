class CompilationError(Exception):
    pass


class ExecutionError(Exception):
    """A failed run. kind: "Runtime Error", "Time Limit Exceeded" or "Memory Limit Exceeded"."""
    def __init__(self, message: str, kind: str = "Runtime Error"):
        super().__init__(message)
        self.kind = kind


class InvalidJSONException(Exception):
    pass

class ConfigurationException(Exception):
    pass

class SolverException(Exception):
    pass