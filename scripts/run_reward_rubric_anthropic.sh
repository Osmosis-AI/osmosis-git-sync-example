#!/usr/bin/env bash
set -euo pipefail

# Example script to run the Anthropic-based rubric scorer
# Requires ANTHROPIC_API_KEY environment variable

python3 -c "
from reward_rubric.reward_rubric_anthropic import compute_rubric_score_anthropic

# Example usage with sample data
solution_str = 'The predicted value is 42'
ground_truth = '42'
extra_info = {'metadata': {'context': 'example test'}}

score = compute_rubric_score_anthropic(
    solution_str=solution_str,
    ground_truth=ground_truth,
    extra_info=extra_info
)

print(f'Anthropic Claude score: {score:.2f} (range 0.0-1.0)')
"
