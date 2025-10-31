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
./scripts/run_reward_rubric.sh  # run the rubric example (requires OPENAI_API_KEY)
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
│   ├── reward_rubric.py
│   ├── reward_rubric_config.yaml
│   ├── reward_rubric_example.json
│   └── sample_data.jsonl
├── .github/
│   └── workflows/
│       └── reward_rubric.yml
├── scripts/
│   └── run_reward_rubric.sh
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

- `reward_rubric.py` defines `@osmosis_rubric score_support_conversation(solution_str, ground_truth, extra_info)`. Supply the rubric text, provider/model identifiers, the assistant reply (`solution_str`), and any optional knobs inside `extra_info`; conversation messages are optional and reconstructed when omitted.
- Delegates scoring to `osmosis_ai.evaluate_rubric`, optionally capturing hosted-model metadata. When `extra_info["capture_details"]` is true the function stores the full response under `extra_info["result_details"]`.
- Use `scripts/run_reward_rubric.sh` to load the sample config and solution, then call the rubric entrypoint without any argparse wrapper.
- `reward_rubric_config.yaml` follows the versioned Osmosis schema (with `version`, `default_*` keys, and `rubrics[]`) and remains available if you want to exercise the official `osmosis` CLI.
- `reward_rubric_example.json` is a sample support response (solution string plus optional context) that can be evaluated locally.
- `sample_data.jsonl` contains JSONL fixtures that pair well with `osmosis preview --path reward_rubric/sample_data.jsonl` if you would like to inspect or score batched conversations with the hosted CLI.

### `sample_data.jsonl` – Rubric dataset

- Mirrors the Osmosis CLI format (`rubric_id`, `conversation_id`, `solution_str`, etc.). Use it with `osmosis preview --path reward_rubric/sample_data.jsonl` or `osmosis eval --data reward_rubric/sample_data.jsonl` whenever you need dataset-driven smoke tests.

### `.github/workflows/`

- `reward_rubric.yml` runs the rubric scorer in GitHub Actions whenever `reward_rubric/reward_rubric.py` or `reward_rubric/reward_rubric_example.json` changes on a push or pull request. The job installs the package, injects an API key via secrets, and executes the rubric script so reviewers can see an automated score.

### `scripts/`

- `run_reward_rubric.sh` loads the YAML preset and JSON example, then calls `reward_rubric.score_support_conversation(solution_str, ground_truth, extra_info)`. Ensure `OPENAI_API_KEY` (or another provider key supported by `osmosis_ai`) is available in the environment before executing.

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

## Running the reward rubric example

```bash
export OPENAI_API_KEY=sk-your-key
./scripts/run_reward_rubric.sh
```

Make sure `osmosis-ai` is installed (run `pip install --upgrade osmosis-ai` if needed). The script passes the built-in preset, but you can supply alternate solution payloads interactively:

```bash
# Point to a different solution payload
./scripts/run_reward_rubric.sh --data path/to/your_solution.json
```

To sanity-check rubric assets without writing Python, install the SDK and use the bundled CLI:

```bash
osmosis preview --path reward_rubric/reward_rubric_config.yaml
osmosis preview --path reward_rubric/sample_data.jsonl
osmosis eval --rubric support_followup --data reward_rubric/sample_data.jsonl --config reward_rubric/reward_rubric_config.yaml
```

The helper script prints a one-line score summary. If you need detailed hosted-model output (explanations, metadata, etc.), run your own Python shell and call `score_support_conversation` with `extra_info["capture_details"] = True`.

## Configuring CI/CD with GitHub Actions

1. **Review the workflow definition:** `.github/workflows/reward_rubric.yml` ships with this repo. It installs the package and runs the rubric scorer so you can see the current score each time the workflow executes.
2. **Create the expected environment:** In your GitHub repository, open **Settings → Environments**, click **New environment**, and name it `osmosis-secrets` (the workflow references this environment).
3. **Add environment secrets:** Inside the `osmosis-secrets` environment, use **Add environment secret** to provide the keys required for evaluation. For this example, set `OPENAI_API_KEY`. If you plan to exercise other hosted models, also add any of `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`, or `XAI_API_KEY`.
4. **Understand the trigger:** Any push or pull request that modifies `reward_rubric/reward_rubric.py` or `reward_rubric/reward_rubric_example.json` automatically runs the workflow so you can check the revised score before merging the change.
5. **Review and re-run:** After each run, open the **Actions** tab to inspect the job logs. Use **Re-run jobs** for the most recent commit, or add a `workflow_dispatch` trigger if you want to run the scorer on demand.

## How Osmosis syncs this repository

1. **MCP tools** – Every function decorated with `@mcp.tool` (or `@mcp.tool()`) inside `mcp/tools/` is ingested, including type hints and docstrings.
2. **Reward functions** – Functions decorated with `@osmosis_reward` in `reward_fn/` become numeric reward hooks for reinforcement learning pipelines.
3. **Reward rubrics** – Functions decorated with `@osmosis_rubric` in `reward_rubric/` are registered so hosted models can score conversations using your rubric text.

Keep type hints, docstrings, and configuration files current so the Osmosis sync remains accurate.
