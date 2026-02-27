import os
import sys
import argparse
import shutil
from CodeWriter.core.solver import Solver
from CodeWriter.utils.logger import get_logger
from CodeWriter.utils.config_loader import Config

def main():
    parser = argparse.ArgumentParser(description="Code Writer — AI-powered code solver")
    parser.add_argument(
        "path",
        help="Path to the problem directory (required)"
    )
    parser.add_argument(
        "--profile",
        type=str,
        help="Config profile to use (overrides CODEWRITER_PROFILE env var)."
    )
    parser.add_argument(
        "--api-key",
        type=str,
        help="API key for Gemini provider (overrides profile api_key)."
    )
    parser.add_argument(
        "--ollama-url",
        type=str,
        help="Ollama server URL/IP for Ollama provider (overrides profile base_url)."
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose (DEBUG level) logging"
    )
    
    args = parser.parse_args()

    # Resolve profile (CLI -> env -> default)
    profile = args.profile or os.getenv("CODEWRITER_PROFILE") or "default"
    os.environ["CODEWRITER_PROFILE"] = profile

    # Initialize logger with requested verbosity
    logger = get_logger(__name__, level=10 if args.verbose else 20)
    logger.info(f"Profile: {profile}")
    path = args.path
    logger.info(f"Starting solver for: {path}")
    # Load merged config to inspect provider and profile settings
    cfg = Config()
    provider = (cfg.get("model", "provider") or "ollama").lower()

    # If gemini profile/provider is used, require an API key (CLI or profile)
    if provider == "gemini":
        profile_key = cfg.get("model", "api_key") or None
        if not (args.api_key or profile_key):
            print("Error: Gemini profile requires --api-key or model.api_key in profile")
            sys.exit(2)

    # If using default profile (Ollama provider), require base_url via --ollama-url
    if profile == "default":
        if not args.ollama_url:
            print("Error: Default profile requires --ollama-url argument")
            sys.exit(2)
        if shutil.which("ollama") is None:
            print("Error: Ollama provider selected but 'ollama' not found in PATH")
            sys.exit(2)

    # Pass CLI-provided api_key and ollama_url into Solver (overrides profile values when provided)
    solver = Solver(path, api_key=args.api_key, ollama_url=args.ollama_url)
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
