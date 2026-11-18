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

Requirements: Docker with Compose, and an LLM: a local [Ollama](https://ollama.com) server, or an API key for Gemini, OpenAI, Mistral or DeepSeek.

```sh
docker compose build
```

Then create your config file, `codewriter.json`, in the project root. It says which LLM to use, and the
program reads its settings only from this file (like `CMakeLists.txt` for CMake):

```sh
cp codewriter.example.json codewriter.json
```

`codewriter.json` is git-ignored, so it's safe to put an API key in it.

### With Ollama

Start Ollama on your machine and download a model:

```sh
ollama serve          # or: brew services start ollama
ollama pull qwen3:14b
```

`codewriter.json`:

```json
{
  "model": {
    "provider": "ollama",
    "model": "qwen3:14b",
    "base_url": "http://host.docker.internal:11434"
  }
}
```

`host.docker.internal` lets the container reach Ollama on your host (use `http://localhost:11434` without
Docker). If you get `Connection refused`, make Ollama listen on all interfaces with `OLLAMA_HOST=0.0.0.0`
and restart it.

### With Gemini

`codewriter.json`:

```json
{
  "model": {
    "provider": "gemini",
    "model": "gemini-3.8-flash",
    "api_key": "YOUR_GEMINI_KEY"
  }
}
```

Get a key in [Google AI Studio](https://aistudio.google.com/apikey).

### With ChatGPT (OpenAI)

`codewriter.json`:

```json
{
  "model": {
    "provider": "openai",
    "model": "gpt-5",
    "api_key": "YOUR_OPENAI_KEY"
  }
}
```

Get a key at [platform.openai.com/api-keys](https://platform.openai.com/api-keys). The API is billed
separately from a ChatGPT subscription. Use any model name from
[OpenAI's model list](https://platform.openai.com/docs/models). `base_url` is optional (default
`https://api.openai.com/v1`); set it to use another OpenAI-compatible server.

### With Mistral or DeepSeek

```json
{
  "models": [
    { "name": "codestral", "provider": "mistral", "model": "codestral-latest", "api_key": "YOUR_MISTRAL_KEY" },
    { "name": "deepseek", "provider": "deepseek", "model": "deepseek-chat", "api_key": "YOUR_DEEPSEEK_KEY" }
  ]
}
```

Get keys at [console.mistral.ai](https://console.mistral.ai) and
[platform.deepseek.com](https://platform.deepseek.com). Model names are listed in
[Mistral's docs](https://docs.mistral.ai/getting-started/models/) and
[DeepSeek's docs](https://api-docs.deepseek.com/quick_start/pricing). `codestral-latest` is Mistral's coding
model; `deepseek-reasoner` is DeepSeek's slower reasoning model.

### Several models

Use `models` (a list) instead of `model` to run the same problem with each model in turn and get a
summary at the end. `name` identifies an entry (it defaults to the `model` value); an entry's own
`parameters` override the global ones.

```json
{
  "models": [
    { "name": "qwen", "provider": "ollama", "model": "qwen3:14b", "base_url": "http://host.docker.internal:11434" },
    { "name": "gemini", "provider": "gemini", "model": "gemini-3.8-flash", "api_key": "YOUR_GEMINI_KEY",
      "parameters": { "max_attempts": 30 } }
  ],
  "parameters": { "max_attempts": 10 }
}
```

```
📊 Summary:
  qwen                 ❌ failed after 10 attempt(s)
  gemini               ✅ passed after 2 attempt(s)
```

`--model qwen` runs only that entry. The exit code is 0 only if every model that ran solved the problem.
The models run one after another in the same problem folder, so `main.cpp` and `out/` are left from the
last model.

### Run a problem

```sh
docker compose run --rm app poetry run python src/main.py resources/factorial
```

## Command-line options

```
python src/main.py <problem_dir> [options]
```

| Option | Description |
|---|---|
| `problem_dir` | Problem folder, e.g. `resources/skretka` (required) |
| `-c`, `--config FILE` | Config file to use (default: `codewriter.json` in the current directory) |
| `-m`, `--model NAME` | Run only the model with this `name` from the config (default: all of them) |
| `--debug` | Print the system prompt and every prompt sent to the LLM, with the conversation size |
| `-v`, `--verbose` | Debug-level logging |

Keep several config files to switch between models, e.g. `--config qwen.json` or `--config gemini.json`.

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

The run is configured by your `codewriter.json`. Anything you leave out comes from the built-in defaults in
`config/settings.json`, and any key from there can be overridden in `codewriter.json`.

| Setting | Meaning |
|---|---|
| `model` or `models` | One model (an object) or several (a list of objects with the keys below) |
| `model.name` | Name used by `--model` and in the summary (default: the `model` value) |
| `model.provider` | `ollama`, `gemini`, `openai`, `mistral` or `deepseek` (required) |
| `model.model` | Model name, e.g. `qwen3:14b`, `gemini-3.8-flash`, `gpt-5`, `codestral-latest`, `deepseek-chat` (required) |
| `model.base_url` | Server URL (required for Ollama; optional for the others, which have built-in defaults) |
| `model.api_key` | API key (required for everything except Ollama) |
| `model.parameters` | Per-model overrides of `parameters` |
| `parameters.max_attempts` | Maximum number of attempts (default 10) |
| `parameters.num_ctx` | Ollama context size in tokens (default 12288). Ollama's own default is often 4096, which silently drops the start of longer conversations. Larger values use more RAM. |
| `parameters.think` | Enable the model's thinking mode (Ollama) |
| `environment.compiler`, `environment.flags` | Compiler and flags; also shown to the model in the system prompt |

The program checks the file at startup and stops with a clear message if a required setting is missing.

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
cp codewriter.example.json codewriter.json   # then edit it
poetry run python src/main.py resources/factorial
```

On Arch Linux, `./install.sh` builds a package (via `PKGBUILD`) that installs a `code-writer` command;
`./uninstall.sh` removes it.

## Project structure

```
src/main.py                     # CLI entry point and the attempt loop
src/CodeWriter/core/
    solver.py                   # builds prompts, extracts code, runs validation
    client.py                   # LLM clients (Ollama, Gemini, OpenAI-compatible: OpenAI, Mistral, DeepSeek)
    compiler.py                 # compiles main.cpp with g++
    runner.py                   # runs the binary on a test with a time limit
    tester.py                   # compares output with expected output
src/CodeWriter/utils/           # config loading, prompt/history, logging, file helpers
codewriter.example.json         # example config; copy to codewriter.json
config/                         # settings.json (defaults), prompts/
resources/                      # problems and their tests
legacy/                         # earlier C++ prototype (not used)
```

## Safety

The app compiles and runs code written by an LLM. Run it in Docker rather than directly on your machine.
