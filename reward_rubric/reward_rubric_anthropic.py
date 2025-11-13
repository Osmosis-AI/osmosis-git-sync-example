from osmosis_ai import (
    evaluate_rubric,
    osmosis_rubric,
)
import os

# make life easier by hardcoding the rubric, score range and model info
RUBRIC = "Reward based on whether the predicted numerical value matches the ground truth."
SCORE_MIN = 0.0
SCORE_MAX = 1.0
PROVIDER = "anthropic"
MODEL = "claude-sonnet-4-5-20250929"
API_KEY = os.getenv("ANTHROPIC_API_KEY")

@osmosis_rubric
def compute_rubric_score_anthropic(
    solution_str: str,
    ground_truth: str,
    extra_info: dict,
    **kwargs
) -> float:
    """
    Delegate rubric scoring to a hosted model while keeping @osmosis_rubric validation.
    """
    model_info = {"provider": PROVIDER, "model": MODEL, "api_key": API_KEY}
    prompt_metadata = extra_info.get("metadata")

    result = evaluate_rubric(
        rubric=RUBRIC,
        solution_str=solution_str,
        model_info=model_info,
        ground_truth=ground_truth,
        metadata=prompt_metadata,
        score_min=SCORE_MIN,
        score_max=SCORE_MAX,
        return_details=False,
    )

    return float(result)