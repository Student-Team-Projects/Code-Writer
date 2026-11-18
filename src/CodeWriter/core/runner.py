from dataclasses import dataclass
import os
import signal
import subprocess
import sys
import time

try:
    import resource
except ImportError:  # not available on Windows
    resource = None

from ..utils.file_validator import FileValidator
from ..utils.exceptions import ExecutionError
from ..utils.logger import get_logger, pretty_print_message

logger = get_logger(__name__)
POLL_INTERVAL = 0.005  # seconds between checks on the running program
MB = 1024 * 1024


@dataclass
class RunResult:
    time: float          # wall-clock seconds
    memory_mb: float     # peak resident memory (see Runner._format_memory for small values)
    soft_tle: bool       # ran longer than the soft time limit (still counts as passed)


class Runner:
    """Runs a solution on one test with a soft time limit, a hard time limit and a memory limit.

    - Hard time limit: the program is killed when it is reached -> "Time Limit Exceeded".
    - Soft time limit: exceeding it still passes; the result is flagged so it can be reported.
    - Memory limit: the address space is capped (Linux), and peak memory is checked after the run
      -> "Memory Limit Exceeded".
    """

    def __init__(self, time_soft: float, time_hard: float, memory_mb: int):
        self.time_soft = time_soft
        self.time_hard = time_hard
        self.memory_mb = memory_mb
        # macOS ignores address-space limits, so memory is only checked after the run there
        self.memory_enforced = sys.platform.startswith("linux")
        if not self.memory_enforced:
            logger.warning("Memory limit is not enforced on %s; peak memory is only checked after each run. "
                           "Use Docker (Linux) for real limits.", sys.platform)

    def _command(self, binary: str) -> list:
        """The command to run. On Linux, a small sh wrapper caps memory (address space and stack) and CPU time,
        then exec's the solution. The stack limit is raised to the memory limit, as on most judges, so deep
        recursion works."""
        if not self.memory_enforced:
            return [binary]
        kb = int(self.memory_mb * 1024)
        cpu = int(self.time_hard) + 1  # backstop; the parent kills the program at the hard limit
        script = (f"ulimit -v {kb} 2>/dev/null; ulimit -s {kb} 2>/dev/null; ulimit -t {cpu} 2>/dev/null; "
                  'exec "$0"')
        return ["/bin/sh", "-c", script, binary]

    def run(self, binary_path: str, input: str, output: str, error: str) -> RunResult:
        validator = FileValidator()

        binary = validator.validate(binary_path, executable=True)
        input_file = validator.validate(input)
        output_file = validator.validate_and_create(output, input_file.parent, input_file.stem)
        error_file = validator.validate_and_create(error, input_file.parent, input_file.stem)

        logger.info("Running: %s (input=%s)", binary, input_file.name)
        with open(input_file, "r") as f_in, open(output_file, "w") as f_out, open(error_file, "w") as f_err:
            baseline_mb = self._own_peak_memory_mb()
            start = time.monotonic()
            process = subprocess.Popen(self._command(str(binary)), stdin=f_in, stdout=f_out, stderr=f_err)
            status, rusage, killed = self._wait(process, start)
            elapsed = time.monotonic() - start

        memory_mb = self._peak_memory_mb(rusage)
        stderr = self._read(error_file)
        stats = f"{elapsed:.3f} s, {self._format_memory(memory_mb, baseline_mb)}"
        limits = f"time limit {self.time_soft:g} s (soft) / {self.time_hard:g} s (hard), memory limit {self.memory_mb} MB"

        if killed:
            return self._fail("Time Limit Exceeded",
                              f"Killed after {elapsed:.3f} s: exceeded the hard {limits}.")

        if memory_mb > self.memory_mb or self._looks_like_mle(status, memory_mb, stderr):
            used = f"Used {memory_mb:.1f} MB" if memory_mb > self.memory_mb else "Memory allocation failed"
            return self._fail("Memory Limit Exceeded", f"{used} ({limits}).\n{stderr}")

        if os.WIFSIGNALED(status):
            sig = os.WTERMSIG(status)
            if sig == getattr(signal, "SIGXCPU", None):
                return self._fail("Time Limit Exceeded",
                                  f"CPU time exceeded after {elapsed:.3f} s ({limits}).")
            try:
                name = signal.Signals(sig).name
            except ValueError:
                name = str(sig)
            return self._fail("Runtime Error", f"Program killed by signal {name} ({stats}).\n{stderr}")

        code = os.WEXITSTATUS(status)
        if code != 0:
            return self._fail("Runtime Error", f"Program exited with code {code} ({stats}).\n{stderr}")

        soft_tle = elapsed > self.time_soft
        if soft_tle:
            logger.warning("⚠️  Soft time limit exceeded: %.3f s > %g s (still counts as passed)",
                           elapsed, self.time_soft)
        else:
            logger.info("Finished in %s", stats)
        return RunResult(time=elapsed, memory_mb=memory_mb, soft_tle=soft_tle)

    def _wait(self, process: subprocess.Popen, start: float):
        """Wait for the process, killing it at the hard time limit. Returns (status, rusage, killed)."""
        killed = False
        while True:
            pid, status, rusage = os.wait4(process.pid, os.WNOHANG)
            if pid:
                process.returncode = status  # tell Popen it's reaped
                return status, rusage, killed
            if not killed and time.monotonic() - start > self.time_hard:
                process.kill()
                killed = True
            time.sleep(POLL_INTERVAL)

    @staticmethod
    def _peak_memory_mb(rusage) -> float:
        # ru_maxrss is in kilobytes on Linux and in bytes on macOS
        peak = rusage.ru_maxrss
        return peak / MB if sys.platform == "darwin" else peak / 1024

    def _own_peak_memory_mb(self) -> float:
        # Only Linux carries the parent's peak over to the child (see _format_memory)
        if resource is None or not sys.platform.startswith("linux"):
            return 0.0
        return self._peak_memory_mb(resource.getrusage(resource.RUSAGE_SELF))

    @staticmethod
    def _format_memory(memory_mb: float, baseline_mb: float) -> str:
        """On Linux a child's peak memory starts at its parent's (this Python process, ~20 MB), because the
        kernel carries the peak over from fork to exec. A peak at that level only means "at most this much".
        Larger peaks are the program's own, so limit checks stay correct as long as the limit is above it."""
        if baseline_mb and memory_mb <= baseline_mb + 1:
            return f"≤ {baseline_mb:.0f} MB"
        return f"{memory_mb:.1f} MB"

    def _looks_like_mle(self, status: int, memory_mb: float, stderr: str) -> bool:
        """With the address space capped, running out of memory shows up as a failed allocation, not high usage."""
        failed = os.WIFSIGNALED(status) or os.WEXITSTATUS(status) != 0
        if not failed:
            return False
        return "bad_alloc" in stderr or (self.memory_enforced and memory_mb > 0.9 * self.memory_mb)

    @staticmethod
    def _read(path) -> str:
        try:
            with open(path, "r", errors="replace") as f:
                return f.read()
        except OSError:
            return ""

    @staticmethod
    def _fail(kind: str, message: str):
        pretty_print_message(kind, message)
        logger.error("%s: %s", kind, message.splitlines()[0])
        raise ExecutionError(message, kind=kind)
