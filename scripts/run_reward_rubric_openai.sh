#!/usr/bin/env bash
set -euo pipefail

# Example script to run the OpenAI-based rubric scorer
# Requires OPENAI_API_KEY environment variable

python3 -c "
from reward_rubric.reward_rubric_openai import compute_rubric_score_openai

# Example usage with sample data
solution_str = 'The predicted value is 42'
ground_truth = '42'
extra_info = {'metadata': {'context': 'example test'}}

score = compute_rubric_score_openai(
    solution_str=solution_str,
    ground_truth=ground_truth,
    extra_info=extra_info
)

print(f'OpenAI GPT score: {score:.2f} (range 0.0-1.0)')
"
