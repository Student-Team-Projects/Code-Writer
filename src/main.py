import os
import sys
import argparse
from CodeWriter.core.solver import Solver
from CodeWriter.utils.logger import get_logger

def main():
    parser = argparse.ArgumentParser(
        description="Code Writer — AI-powered code solver",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  poetry run python src/main.py resources/factorial
  poetry run python src/main.py resources/factorial --profile gemini
  poetry run python src/main.py resources/factorial --profile default -v
  CODEWRITER_PROFILE=gemini poetry run python src/main.py resources/factorial
        """
    )
    parser.add_argument(
        "path",
        nargs="?",
        default="resources/factorial",
        help="Path to the problem directory (default: resources/factorial)"
    )
    parser.add_argument(
        "--profile",
        type=str,
        help="Config profile to use (default, gemini, or custom). Overrides CODEWRITER_PROFILE env var."
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose (DEBUG level) logging"
    )
    
    args = parser.parse_args()
    
    # Set profile from CLI argument BEFORE creating logger or Solver
    # This ensures config_loader reads the correct profile
    if args.profile:
        os.environ["CODEWRITER_PROFILE"] = args.profile
    elif "CODEWRITER_PROFILE" not in os.environ:
        os.environ["CODEWRITER_PROFILE"] = "default"
    
    # Now initialize logger (after profile is set)
    logger = get_logger(__name__)
    logger.info(f"Profile: {os.environ.get('CODEWRITER_PROFILE')}")
    
    # Set verbose logging if requested
    if args.verbose:
        from CodeWriter.utils.logger import get_logger as get_logger_fresh
        logger = get_logger_fresh(__name__, level=10)  # logging.DEBUG = 10
        logger.info("Verbose mode enabled")
    
    path = args.path
    
    logger.info(f"Starting solver for: {path}")
    solver = Solver(path)
    tries = 0
    
    while tries < solver.timeout:
        if tries == 0:
            logger.info("🔄 Attempt 1: Generating initial solution...")
            result = solver.begin_chat()
        else:
            logger.info(f"🔄 Attempt {tries + 1}: Fixing errors...")
            result = solver.continue_chat()
        
        logger.info("✓ Running validation...")
        public = solver.validate_public()
        secret = solver.validate_secret()
        
        if public and secret:
            logger.info("✅ All tests passed! Solution is correct.")
            exit(0)
        
        tries += 1
    
    logger.error(f"❌ Failed after {solver.timeout} attempts")
    exit(1)

if __name__ == "__main__":
    main()
