import sys
import argparse
from CodeWriter.core.solver import Solver
from CodeWriter.utils.logger import get_logger
from CodeWriter.utils.config_loader import Config
from CodeWriter.utils.exceptions import SolverException, ConfigurationException


def solve(path: str, model: dict, debug: bool, logger) -> dict:
    """Run the attempt loop for one model.

    Returns {"passed": bool, "attempts": int, "error": str | None, "soft_tle": [tests over the soft time limit]}.
    """
    try:
        solver = Solver(path, model, debug=debug)
    except ConfigurationException as e:
        logger.error(f"❌ {e}")
        sys.exit(2)

    for attempt in range(1, solver.max_attempts + 1):
        try:
            if attempt == 1:
                logger.info("🔄 Attempt 1: Generating initial solution...")
                solver.begin_chat()
            else:
                logger.info(f"🔄 Attempt {attempt}: Fixing errors...")
                solver.continue_chat()
        except SolverException as e:
            logger.error(f"❌ {e}")
            return {"passed": False, "attempts": attempt, "error": str(e), "soft_tle": []}

        logger.info("✓ Running validation...")
        public = solver.validate_public()
        # Skip secret tests when public ones fail, so the model gets the visible failure details
        secret = public and solver.validate_secret()

        if public and secret:
            if solver.soft_tle:
                slowest = max(t["time"] for t in solver.soft_tle)
                logger.warning(f"⚠️  Passed, but {len(solver.soft_tle)} test(s) exceeded the soft time limit "
                               f"of {solver.limits['time_soft']:g} s (slowest {slowest:.3f} s)")
            logger.info("✅ All tests passed! Solution is correct.")
            return {"passed": True, "attempts": attempt, "error": None, "soft_tle": solver.soft_tle}

    logger.error(f"❌ Failed after {solver.max_attempts} attempts")
    return {"passed": False, "attempts": solver.max_attempts, "error": None, "soft_tle": []}


def main():
    parser = argparse.ArgumentParser(description="Code Writer — AI-powered code solver")
    parser.add_argument(
        "path",
        help="Path to the problem directory (required)"
    )
    parser.add_argument(
        "-c", "--config",
        type=str,
        help="Path to the config file (default: ./codewriter.json)"
    )
    parser.add_argument(
        "-m", "--model",
        type=str,
        help="Run only the model with this name from the config (default: all models)"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose (DEBUG level) logging"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Print every prompt sent to the LLM"
    )

    args = parser.parse_args()

    # Initialize logger with requested verbosity
    logger = get_logger(__name__, level=10 if args.verbose else 20)

    try:
        cfg = Config.load(args.config)
        models = cfg.models(args.model)
    except ConfigurationException as e:
        logger.error(f"❌ {e}")
        sys.exit(2)

    logger.info(f"Config: {cfg.path}")
    logger.info(f"Starting solver for: {args.path}")

    results = {}
    for model in models:
        logger.info(f"🤖 Model: {model['name']} ({model['provider']} / {model['model']})")
        results[model["name"]] = solve(args.path, model, args.debug, logger)

    if len(models) > 1:
        logger.info("📊 Summary:")
        for name, r in results.items():
            status = "✅ passed" if r["passed"] else "❌ failed"
            detail = f" ({r['error']})" if r["error"] else ""
            if r["soft_tle"]:
                detail += f" ⚠️  {len(r['soft_tle'])} test(s) over soft time limit"
            logger.info(f"  {name:20} {status} after {r['attempts']} attempt(s){detail}")

    # Exit 0 only if every model solved the problem
    sys.exit(0 if all(r["passed"] for r in results.values()) else 1)


if __name__ == "__main__":
    main()
