# Example Repository for Osmosis GitHub Sync

This repository demonstrates the layout and code artifacts that the Osmosis GitHub integration discovers and syncs. It bundles a FastMCP tool server, a numeric reward function, and a rubric-based scorer so you can exercise every integration surface locally before connecting to Osmosis.

## Requirements

- Python 3.12 (matches `pyproject.toml`)
- Install project dependencies with `pip install .`; for editable installs use `pip install -e .` or `uv pip install .`

## Quick Start

```bash
# Optional: create a virtual environment first
pip install -e .           # install the package and dependencies
python mcp/main.py &       # start the FastMCP server on 0.0.0.0:8080
python mcp/test/test.py    # list the published tools
./scripts/run_reward_rubric_openai.sh  # run the OpenAI rubric example (requires OPENAI_API_KEY)
# or
./scripts/run_reward_rubric_anthropic.sh  # run the Anthropic rubric example (requires ANTHROPIC_API_KEY)
```

Stop the MCP server with `Ctrl+C` when you are done, or pass `--host/--port` if you need to bind to a different interface.

## Repository Layout

```
osmosis-git-sync-example/
├── mcp/
│   ├── main.py
│   ├── server/
│   │   ├── __init__.py
│   │   └── mcp_server.py
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── api_helpers.py
│   │   ├── math.py
│   │   └── ml_utils.py
│   └── test/
│       └── test.py
├── reward_fn/
│   └── compute_reward.py
├── reward_rubric/
│   ├── reward_rubric_anthropic.py
│   └── reward_rubric_openai.py
├── .github/
│   └── workflows/
│       └── reward_rubric.yml
├── scripts/
│   ├── run_reward_rubric_anthropic.sh
│   └── run_reward_rubric_openai.sh
├── LICENSE.md
├── pyproject.toml
├── uv.lock
└── README.md
```

### `mcp/` – FastMCP tools and server

- `main.py` starts the FastMCP HTTP transport (`python mcp/main.py`) and accepts `--host/--port`.
- `server/mcp_server.py` instantiates `FastMCP("OsmosisTools")` and exposes a `/health` route.
- `tools/__init__.py` exposes every `.py` module in the folder via `__all__`, so `from tools import *` eagerly loads each tool module.
- Tool modules:
  - `math.multiply(first_val, second_val)` multiplies two numbers and rounds to four decimals.
  - `api_helpers.validate_api_request(...)` validates required/empty fields.
  - `api_helpers.format_api_response(...)` wraps payloads in a consistent envelope.
  - `api_helpers.paginate_results(...)` slices item lists and returns pagination metadata.
  - `ml_utils.calculate_similarity(...)` computes cosine similarity.
  - `ml_utils.normalize_features(...)` performs min–max normalization on selected fields.
  - `ml_utils.return_true()` always returns `True`; useful for sanity checks.
  - `ml_utils.cluster_analysis(...)` (async) produces a toy clustering summary for supplied data.
- `test/test.py` shows how to connect with `fastmcp.Client` and list the published tools.

### `reward_fn/` – Numeric reward functions

- `compute_reward.py` implements `@osmosis_reward numbers_match_reward(...)`.
  - `extract_solution` grabs the first numeric token that follows a markdown-style `####` heading and returns it as text.
  - The reward converts the extracted token and ground truth to floats, awarding `1.0` when they match within `1e-7` and `0.0` otherwise (including extraction failures).

### `reward_rubric/` – Rubric-based scoring

This folder contains simplified, provider-specific rubric scoring examples that demonstrate how to use `@osmosis_rubric` with different LLM providers:

- **`reward_rubric_anthropic.py`** – Uses Anthropic's Claude (claude-sonnet-4-5-20250929) for rubric evaluation. Requires `ANTHROPIC_API_KEY` environment variable.
- **`reward_rubric_openai.py`** – Uses OpenAI's GPT (gpt-5-mini) for rubric evaluation. Requires `OPENAI_API_KEY` environment variable.

Both files:
- Define an `@osmosis_rubric` decorated function that delegates scoring to `osmosis_ai.evaluate_rubric`
- Use hardcoded rubric text, score ranges (0.0-1.0), and model configurations for simplicity
- Can be imported and called directly in your Python code or executed as standalone modules
- Accept `solution_str` (the text to evaluate), `ground_truth` (reference answer), and `extra_info` (metadata dictionary)

### `.github/workflows/`

- `reward_rubric.yml` runs the rubric scorers in GitHub Actions whenever files in `reward_rubric/` change on a push or pull request. The job installs the package, injects API keys via secrets, and executes both rubric scripts so reviewers can see automated scores from multiple providers.

### `scripts/`

- `run_reward_rubric_openai.sh` executes the OpenAI-based rubric scorer. Ensure `OPENAI_API_KEY` is available in the environment before executing.
- `run_reward_rubric_anthropic.sh` executes the Anthropic-based rubric scorer. Ensure `ANTHROPIC_API_KEY` is available in the environment before executing.

## Installing dependencies

```bash
# From the repository root
pip install .
# or install in editable mode
pip install -e .
# or, if you use uv
uv pip install .
```

## Running the MCP server

```bash
# Default: 0.0.0.0:8080
python mcp/main.py

# Custom host/port
python mcp/main.py --host 127.0.0.1 --port 3000

# Health check
curl http://localhost:8080/health
```

## Exercising the MCP tools locally

```bash
python mcp/test/test.py
```

The script connects to `http://0.0.0.0:8080/mcp`, confirms the session, and lists the registered tools.

## Running the reward rubric examples

Make sure `osmosis-ai` is installed (run `pip install --upgrade osmosis-ai` if needed).

### Using OpenAI (GPT)

```bash
export OPENAI_API_KEY=sk-your-key
./scripts/run_reward_rubric_openai.sh
```

Or call the function directly in Python:

```python
from reward_rubric.reward_rubric_openai import compute_rubric_score_openai

score = compute_rubric_score_openai(
    solution_str="The predicted value is 42",
    ground_truth="42",
    extra_info={"metadata": {"context": "test"}}
)
print(f"Score: {score}")
```

### Using Anthropic (Claude)

```bash
export ANTHROPIC_API_KEY=sk-ant-your-key
./scripts/run_reward_rubric_anthropic.sh
```

Or call the function directly in Python:

```python
from reward_rubric.reward_rubric_anthropic import compute_rubric_score_anthropic

score = compute_rubric_score_anthropic(
    solution_str="The predicted value is 42",
    ground_truth="42",
    extra_info={"metadata": {"context": "test"}}
)
print(f"Score: {score}")
```

Both scripts will evaluate whether the solution matches the ground truth and return a score between 0.0 and 1.0.

## Configuring CI/CD with GitHub Actions

1. **Review the workflow definition:** `.github/workflows/reward_rubric.yml` ships with this repo. It installs the package and runs the rubric scorers so you can see the current scores each time the workflow executes.
2. **Create the expected environment:** In your GitHub repository, open **Settings → Environments**, click **New environment**, and name it `osmosis-secrets` (the workflow references this environment).
3. **Add environment secrets:** Inside the `osmosis-secrets` environment, use **Add environment secret** to provide the keys required for evaluation. Add both `OPENAI_API_KEY` and `ANTHROPIC_API_KEY` to test both providers. You can also add `GOOGLE_API_KEY` or `XAI_API_KEY` if you plan to extend the examples.
4. **Understand the trigger:** Any push or pull request that modifies files in `reward_rubric/` automatically runs the workflow so you can check the revised scores before merging the change.
5. **Review and re-run:** After each run, open the **Actions** tab to inspect the job logs. Use **Re-run jobs** for the most recent commit, or add a `workflow_dispatch` trigger if you want to run the scorer on demand.

## How Osmosis syncs this repository

1. **MCP tools** – Every function decorated with `@mcp.tool` (or `@mcp.tool()`) inside `mcp/tools/` is ingested, including type hints and docstrings.
2. **Reward functions** – Functions decorated with `@osmosis_reward` in `reward_fn/` become numeric reward hooks for reinforcement learning pipelines.
3. **Reward rubrics** – Functions decorated with `@osmosis_rubric` in `reward_rubric/` are registered so hosted models can score conversations using your rubric text.

Keep type hints, docstrings, and configuration files current so the Osmosis sync remains accurate.
