#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

python "${REPO_ROOT}/reward_rubric/reward_rubric.py" --config "${REPO_ROOT}/reward_rubric/reward_rubric_config.yaml"
