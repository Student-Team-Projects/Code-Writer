# Code Writer

**Authors:** Helena Arendacz, Jakub Janór, Piotr Pasula, Szymon Trofimiec
**Supervision:** Batłomiej Bosek
**Task board:** [Microsoft Planner](https://planner.cloud.microsoft/ui/web/plan/tKDxzTuwO0uz3KdscbwahpYABVtD/view/board?tid=eb0e26eb-bfbe-47d2-9e90-ebd2426dbceb)

Code Writer uses an LLM to solve competitive-programming problems in C++. It gives the model a problem
statement with example tests, compiles the answer, runs it against the tests, and feeds any failure back
to the model until the solution passes or the attempt limit is reached.

## How it works

```
problem_description.txt + public examples
        │
        ▼
   ┌─────────┐  code   ┌─────────┐  binary  ┌────────────────────────┐
   │   LLM   │ ──────▶ │   g++   │ ───────▶ │ run public tests       │
   └─────────┘         └─────────┘          │ then secret tests      │
        ▲                   │ errors        └────────────────────────┘
        │                   ▼                          │ failure
        └──────── error report (compiler output, ◀─────┘
                  failing input / output / expected)
```

1. The model gets the system prompt (`config/prompts/system.txt`) and the task (`config/prompts/user_task.txt`),
   with the problem description and all public test inputs and outputs filled in.
2. The C++ code is extracted from the reply and saved as `main.cpp` in the problem folder.
3. It is compiled with the configured flags (`-O3 -Wall -Wshadow -Wextra -Werror` by default).
4. The binary runs on every public test (15 s limit each). Output is compared ignoring whitespace differences.
5. If all public tests pass, the secret tests run. The model never sees their contents.
6. On failure, the model gets an error report (`config/prompts/error_fix.txt`) with the compiler output,
   the crash reason, or the failing test's input, output and expected output. Secret failures are reported
   only as "This test is secret". The loop goes back to step 2.

It stops when all tests pass (exit code 0) or after the maximum number of attempts (exit code 1).

## Quick start (Docker)

Requirements: Docker with Compose, and an LLM: a local [Ollama](https://ollama.com) server or a Gemini API key.

```sh
docker compose build
```

### With Ollama (default profile)

Start Ollama on your machine and download the model used by the default profile:

```sh
ollama serve          # or: brew services start ollama
ollama pull qwen3:14b
```

Then run a problem:

```sh
docker compose run --rm app poetry run python src/main.py resources/factorial \
    --ollama-url http://host.docker.internal:11434
```

`host.docker.internal` lets the container reach Ollama on your host. If you get `Connection refused`, make
Ollama listen on all interfaces with `OLLAMA_HOST=0.0.0.0` and restart it.

### With Gemini

```sh
docker compose run --rm app poetry run python src/main.py resources/factorial \
    --profile gemini --api-key YOUR_GEMINI_KEY
```

Get a key in [Google AI Studio](https://aistudio.google.com/apikey). Pass it on the command line;
**don't put it in `config/profiles/gemini.json`**, which is committed to git.

## Command-line options

```
python src/main.py <problem_dir> [options]
```

| Option | Description |
|---|---|
| `problem_dir` | Problem folder, e.g. `resources/skretka` (required) |
| `--profile NAME` | Config profile from `config/profiles/` (`default` = Ollama, `gemini`) |
| `--ollama-url URL` | Ollama server URL (required with the `default` profile) |
| `--api-key KEY` | Gemini API key |
| `--debug` | Print the system prompt and every prompt sent to the LLM, with the conversation size |
| `-v`, `--verbose` | Debug-level logging |

The profile is chosen from `--profile`, then the `CODEWRITER_PROFILE` environment variable, then
`active_profile` in `config/settings.json`.

## Problems

Problems live in `resources/`. Each problem is a folder:

```
resources/<problem>/
├── problem_description.txt   # statement given to the model
├── tests_public/             # shown to the model as examples, and run
│   ├── in/1                  # stdin for test 1
│   └── expected/1            # expected stdout for test 1
└── tests_secret/             # run only after public tests pass; never shown to the model
    ├── in/1
    └── expected/1
```

Tests are matched by file name (`in/N` ↔ `expected/N`). If `tests_secret/` is missing, the secret tests are
skipped with a warning. Copy `resources/template` to start a new problem.

Available problems: `factorial`, `primes`, `prime-reduction`, `order`, `big-int-division`, `skretka`.

A run writes these files into the problem folder (they are git-ignored): `main.cpp` (the last generated
solution), `main` (the binary), and `out/` and `error/` in each test folder (the program's stdout and stderr
per test).

## Configuration

`config/settings.json` holds the defaults, and each file in `config/profiles/` overrides them. The main settings:

| Setting | Meaning |
|---|---|
| `model.provider` | `ollama` or `gemini` |
| `model.model` | Model name, e.g. `qwen3:14b`, `gemini-3.8-flash` |
| `model.base_url` | Ollama server URL (overridden by `--ollama-url`) |
| `parameters.timeout` | **Maximum number of attempts** (not seconds) |
| `parameters.num_ctx` | Ollama context size in tokens (default 12288). Ollama's own default is often 4096, which silently drops the start of longer conversations. Larger values use more RAM. |
| `parameters.think` | Enable the model's thinking mode (Ollama) |
| `environment.compiler`, `environment.flags` | Compiler and flags; also shown to the model in the system prompt |

To manage profiles:

```sh
python config_manager.py list            # list profiles
python config_manager.py view gemini     # show a profile
python config_manager.py switch gemini   # set active_profile in settings.json
python config_manager.py current         # show the active profile
```

## Debugging a run

- `--debug` shows exactly what the model receives each round, including the error reports.
- `-v` adds debug logging.
- After a run, look at `main.cpp` and `tests_*/out/`, `tests_*/error/` in the problem folder.

## Running without Docker

Docker is recommended: the generated code often uses `<bits/stdc++.h>`, which is only available with GCC
(not with Apple's clang, which is what `g++` runs on macOS).

On Linux with Python 3.12, `g++` and [Poetry](https://python-poetry.org):

```sh
poetry install --no-root
poetry run python src/main.py resources/factorial --ollama-url http://localhost:11434
```

On Arch Linux, `./install.sh` builds a package (via `PKGBUILD`) that installs a `code-writer` command;
`./uninstall.sh` removes it.

## Project structure

```
src/main.py                     # CLI entry point and the attempt loop
src/CodeWriter/core/
    solver.py                   # builds prompts, extracts code, runs validation
    client.py                   # Ollama and Gemini clients
    compiler.py                 # compiles main.cpp with g++
    runner.py                   # runs the binary on a test with a time limit
    tester.py                   # compares output with expected output
src/CodeWriter/utils/           # config loading, prompt/history, logging, file helpers
config/                         # settings.json, profiles/, prompts/
resources/                      # problems and their tests
legacy/                         # earlier C++ prototype (not used)
```

## Safety

The app compiles and runs code written by an LLM. Run it in Docker rather than directly on your machine.
