# Example Repository for Osmosis GitHub Sync

This repository demonstrates the layout and code artifacts that the Osmosis GitHub integration discovers and syncs. It bundles a FastMCP tool server, a numeric reward function, and a rubric-based scorer so you can exercise every integration surface locally before connecting to Osmosis.

## Requirements

- Python 3.10+ (3.12 recommended, matches `pyproject.toml`)
- Install dependencies: `pip install "osmosis-ai[mcp]"` (or `uv add "osmosis-ai[mcp]"`)

## Quick Start

```bash
# Optional: create a virtual environment first
pip install "osmosis-ai[mcp]"   # install dependencies

# Evaluate MCP tools against the sample dataset (requires OPENAI_API_KEY)
osmosis eval --mcp ./mcp -d test_data.jsonl \
    --eval-fn reward_fn.compute_reward:numbers_match_reward \
    --model my-finetuned-model \
    --base-url http://localhost:1234/v1

# Or test without eval functions
osmosis test --mcp ./mcp -d test_data.jsonl --model openai/gpt-5-mini

# Start the MCP server directly (for other use cases)
python mcp/main.py &       # start the FastMCP server on 0.0.0.0:8080
python mcp/test/test.py    # list the published tools

# Run the rubric examples
./scripts/run_reward_rubric_openai.sh      # requires OPENAI_API_KEY
./scripts/run_reward_rubric_anthropic.sh   # requires ANTHROPIC_API_KEY
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
│   │   └── math.py
│   └── test/
│       └── test.py
├── reward_fn/
│   └── compute_reward.py
├── reward_rubric/
│   ├── reward_rubric_anthropic.py
│   ├── reward_rubric_openai.py
│   └── reward_rubric_xai.py
├── .github/
│   └── workflows/
│       └── reward_rubric.yml
├── scripts/
│   ├── run_reward_rubric_anthropic.sh
│   └── run_reward_rubric_openai.sh
├── test_data.jsonl           ← sample dataset for osmosis eval/test
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
- `test/test.py` shows how to connect with `fastmcp.Client` and list the published tools.

### `reward_fn/` – Numeric reward functions

- `compute_reward.py` defines `numbers_match_reward(...)` decorated with `@osmosis_reward`.
  - `extract_solution` grabs the first numeric token that follows a markdown-style `####` heading and returns it as text.
  - The reward converts the extracted token and ground truth to floats, awarding `1.0` when they match within `1e-7` and `0.0` otherwise (including extraction failures).

### `reward_rubric/` – Rubric-based scoring

This folder contains simplified, provider-specific rubric scoring examples that demonstrate how to use `@osmosis_rubric` with different LLM providers:

- **`reward_rubric_anthropic.py`** – Uses Anthropic's Claude (claude-sonnet-4-5-20250929) for rubric evaluation. Requires `ANTHROPIC_API_KEY` environment variable.
- **`reward_rubric_openai.py`** – Uses OpenAI's GPT (gpt-5-mini) for rubric evaluation. Requires `OPENAI_API_KEY` environment variable.
- **`reward_rubric_xai.py`** – Uses xAI's Grok (grok-4-fast-non-reasoning) for rubric evaluation. Requires `XAI_API_KEY` environment variable.

All files:
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
# Local Rollout (MCP tools) — recommended for this repo
pip install "osmosis-ai[mcp]"

# Or, if you use uv
uv add "osmosis-ai[mcp]"

# Other install extras:
# pip install osmosis-ai            # Core SDK only
# pip install "osmosis-ai[server]"  # FastAPI server for Remote Rollout
# pip install "osmosis-ai[full]"    # All features
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

Make sure dependencies are installed (see [Installing dependencies](#installing-dependencies)).

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

## Local Eval & Test with `osmosis eval` / `osmosis test`

Git-sync users can evaluate and test their MCP tools locally using `--mcp`, without writing a `RolloutAgentLoop`. The SDK loads all `@mcp.tool()` functions from the `mcp/` directory and runs a standard agent loop automatically.

### Prerequisites

```bash
pip install "osmosis-ai[mcp]"
```

### Evaluating with `osmosis eval`

`osmosis eval` runs your MCP tools against a dataset, scores each run with eval functions, and reports aggregated metrics (mean, std, pass@k).

```bash
# Basic eval — uses reward_fn/compute_reward.py as the eval function
osmosis eval \
    --mcp ./mcp \
    -d test_data.jsonl \
    --eval-fn reward_fn.compute_reward:numbers_match_reward \
    --model openai/gpt-5-mini

# Eval against a trained model endpoint
osmosis eval \
    --mcp ./mcp \
    -d test_data.jsonl \
    --eval-fn reward_fn.compute_reward:numbers_match_reward \
    --model my-finetuned-model \
    --base-url http://localhost:8000/v1

# Compare trained model vs GPT-5-mini baseline (win/loss/tie report)
osmosis eval \
    --mcp ./mcp \
    -d test_data.jsonl \
    --eval-fn reward_fn.compute_reward:numbers_match_reward \
    --model my-finetuned-model --base-url http://localhost:8000/v1 \
    --baseline-model openai/gpt-5-mini

# Compare two serving endpoints
osmosis eval \
    --mcp ./mcp \
    -d test_data.jsonl \
    --eval-fn reward_fn.compute_reward:numbers_match_reward \
    --model my-model-v2 --base-url http://localhost:8000/v1 \
    --baseline-model my-model-v1 --baseline-base-url http://localhost:8001/v1

# pass@5 analysis with concurrent execution
osmosis eval \
    --mcp ./mcp \
    -d test_data.jsonl \
    --eval-fn reward_fn.compute_reward:numbers_match_reward \
    --model openai/gpt-5-mini \
    --n 5 --batch-size 5

# Save results to JSON
osmosis eval \
    --mcp ./mcp \
    -d test_data.jsonl \
    --eval-fn reward_fn.compute_reward:numbers_match_reward \
    --model openai/gpt-5-mini \
    -o eval_results.json
```

### Testing with `osmosis test`

`osmosis test` runs your MCP tools against a dataset and reports per-row pass/fail, token usage, and latency — useful for validating agent behavior before training.

```bash
# Basic test
osmosis test \
    --mcp ./mcp \
    -d test_data.jsonl \
    --model openai/gpt-5-mini

# Interactive debugging — step through each LLM call
osmosis test \
    --mcp ./mcp \
    -d test_data.jsonl \
    --model openai/gpt-5-mini \
    --interactive

# Jump to a specific row in interactive mode
osmosis test \
    --mcp ./mcp \
    -d test_data.jsonl \
    --model openai/gpt-5-mini \
    --interactive --row 3

# Test a subset of rows
osmosis test \
    --mcp ./mcp \
    -d test_data.jsonl \
    --model openai/gpt-5-mini \
    --limit 2 --offset 1

# Save results to JSON
osmosis test \
    --mcp ./mcp \
    -d test_data.jsonl \
    --model openai/gpt-5-mini \
    -o test_results.json
```

### How `--mcp` works

When you pass `--mcp ./mcp`, the SDK:

1. Imports `mcp/main.py`, which triggers all `@mcp.tool()` registrations
2. Discovers registered tools (e.g. `multiply`) and converts them to OpenAI function-calling schemas
3. Runs a built-in agent loop that calls the LLM, executes tool calls against your MCP functions, and repeats until the LLM stops calling tools or `--max-turns` is reached

This means you can iterate on your tools and reward functions locally, then push to GitHub for Osmosis to sync — no `RolloutAgentLoop` code needed.

> **Note:** `--mcp` and `-m/--module` are mutually exclusive. Use `--mcp` for git-sync projects; use `-m` for remote-rollout projects that implement `RolloutAgentLoop`.

### Model naming convention

Models can be specified in two formats:

- **Simple**: `gpt-5-mini` (auto-prefixed to `openai/gpt-5-mini`)
- **LiteLLM format**: `provider/model` (e.g., `anthropic/claude-sonnet-4-5`)

See [LiteLLM Providers](https://docs.litellm.ai/docs/providers) for the full list of supported providers.

### Supported dataset formats

The `-d/--dataset` flag accepts three formats:

- **Parquet** (recommended) — compact and fast for large datasets
- **JSONL** — one JSON object per line (used in this repo)
- **CSV** — comma-separated values with a header row

Each row must contain: `system_prompt`, `user_prompt`, and `ground_truth` columns. Any additional columns are passed as metadata to your agent and reward functions.

## Additional CLI Commands

### Authentication

Log in to the Osmosis platform for workspace management and training run submission:

```bash
osmosis login                    # Opens browser for authentication
osmosis logout                   # End session and revoke credentials
osmosis whoami                   # Show current user and workspaces
osmosis workspace list           # List all logged-in workspaces
osmosis workspace switch <name>  # Switch to a different workspace
```

### Previewing rubrics and datasets

```bash
osmosis preview --path test_data.jsonl              # Preview a dataset
```

### Evaluating with `osmosis eval-rubric`

`osmosis eval-rubric` evaluates conversations against hosted rubric configurations. This is separate from `osmosis eval`, which runs eval functions against agent datasets.

```bash
osmosis eval-rubric --rubric support_followup --data test_data.jsonl
```

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
