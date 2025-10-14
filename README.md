# Example Repository for Osmosis GitHub Sync

This repository demonstrates the layout and code artifacts that the Osmosis GitHub integration discovers and syncs. It bundles a FastMCP tool server, a numeric reward function, and a rubric-based scorer so you can exercise every integration surface locally before connecting to Osmosis.

## Requirements

- Python 3.12 (matches `pyproject.toml`)
- Install project dependencies with `pip install .`; for editable installs use `pip install -e .` or `uv pip install .`

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
│   └── reward_rubric_example.json
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
- `tools/__init__.py` auto-imports every `@mcp.tool` decorated function so the server exposes them.
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
  - `extract_solution` looks for answers after `####` and returns the numeric token.
  - The reward converts both strings to floats and returns `1.0` when they match within `1e-7`, else `0.0`.

### `reward_rubric/` – Rubric-based scoring

- `reward_rubric.py` defines `@osmosis_rubric score_support_conversation(...)`.
  - Delegates scoring to `osmosis_ai.evaluate_rubric`, optionally capturing detailed metadata via `extra_info`.
  - Provides a `main()` helper that loads `reward_rubric_example.json` and prints the score.
- `reward_rubric_config.yaml` stores the rubric prompt, score range, ground truth summary, and default model info.
- `reward_rubric_example.json` is a sample support conversation that can be evaluated locally.

### `.github/workflows/` 

- `reward_rubric.yml` runs the rubric scorer in GitHub Actions whenever `reward_rubric/reward_rubric_config.yaml` changes on a push or pull request. The job installs the package, injects an API key via secrets, and executes the rubric script so reviewers can see an automated score.

### `scripts/`

- `run_reward_rubric.sh` runs the rubric example (`python reward_rubric/reward_rubric.py --config ...`). Ensure `OPENAI_API_KEY` (or another provider key supported by `osmosis_ai`) is available in the environment before executing.

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

The script passes the default config file, but the scorer now accepts additional flags:

```bash
python reward_rubric/reward_rubric.py \
  --config path/to/custom_config.yaml \
  --messages path/to/messages.json \
  --no-capture-details  # optional
```

Omit `--no-capture-details` to include the hosted model's explanation in the output. If the API key is missing, the script still produces descriptive error messages about the requirement.

## Configuring CI/CD with GitHub Actions

1. **Add the API key secret:** In your GitHub repository, open **Settings → Secrets and variables → Actions**, click **New repository secret**, name it `OPENAI_API_KEY`, and paste the same key you use locally. GitHub encrypts it and only exposes it to workflow runs.
2. **Understand the workflow trigger:** `.github/workflows/reward_rubric.yml` runs automatically on pushes and pull requests that touch `reward_rubric/reward_rubric_config.yaml`, keeping rubric edits validated without running on unrelated changes.
3. **Review the CI output:** After pushing a change, check the **Actions** tab. The job `Reward Rubric Score` installs dependencies, runs `python reward_rubric/reward_rubric.py --config reward_rubric/reward_rubric_config.yaml`, and surfaces success or failure details in the logs.
4. **Re-run or trigger manually:** From the workflow run page you can click **Re-run jobs** to execute the latest code or secrets again. To test on demand, add a `workflow_dispatch` trigger so you can launch the job with the **Run workflow** button.

## How Osmosis syncs this repository

1. **MCP tools** – Every function decorated with `@mcp.tool` (or `@mcp.tool()`) inside `mcp/tools/` is ingested, including type hints and docstrings.
2. **Reward functions** – Functions decorated with `@osmosis_reward` in `reward_fn/` become numeric reward hooks for reinforcement learning pipelines.
3. **Reward rubrics** – Functions decorated with `@osmosis_rubric` in `reward_rubric/` are registered so hosted models can score conversations using your rubric text.

Keep type hints, docstrings, and configuration files current so the Osmosis sync remains accurate.
