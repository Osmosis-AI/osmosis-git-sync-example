from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from osmosis_ai import (
    MissingAPIKeyError,
    ModelNotFoundError,
    ProviderRequestError,
    evaluate_rubric,
    osmosis_rubric,
)

CONFIG_PATH: Path = Path(__file__).with_name("reward_rubric_config.yaml")
MESSAGES_PATH: Path = Path(__file__).with_name("reward_rubric_example.json")


def _load_config(config_path: Path = CONFIG_PATH) -> Dict[str, Any]:
    with config_path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


_CONFIG: Dict[str, Any] = _load_config()

RUBRIC: str = _CONFIG["rubric"]
SCORE_MIN: float = float(_CONFIG.get("score_min", 0.0))
SCORE_MAX: float = float(_CONFIG.get("score_max", 1.0))
GROUND_TRUTH: str = _CONFIG["ground_truth"]
DEFAULT_MODEL_INFO: Dict[str, str] = dict(
    _CONFIG.get("default_model_info", {"provider": "openai", "model": "gpt-5-mini"})
)


@osmosis_rubric
def score_support_conversation(
    model_info: Dict[str, Any],
    rubric: str,
    messages: List[Dict[str, Any]],
    ground_truth: Optional[str] = None,
    system_message: Optional[str] = None,
    extra_info: Dict[str, Any] = None,
    score_min: float = SCORE_MIN,
    score_max: float = SCORE_MAX,
) -> float:
    """Score a support conversation against the rubric using a hosted model.

    The @osmosis_rubric decorator validates the inputs and integrates with the
    Osmosis platform. This helper forwards the scoring request to
    ``osmosis_ai.evaluate_rubric`` and returns the numeric score.

    Args:
        model_info: Provider and model configuration used for evaluation.
        rubric: Rubric text that defines the evaluation criteria.
        messages: Conversation messages to score.
        ground_truth: Optional expected outcome used in rubric evaluation.
        system_message: Optional system prompt to include in the request.
        extra_info: Mutable metadata passed through the evaluation pipeline. If
            ``capture_details`` is set to True, this dictionary is updated in
            place with a ``result_details`` entry containing the full response
            payload from the hosted model.
        score_min: Lower bound for the score range.
        score_max: Upper bound for the score range.

    Returns:
        float: The evaluated score within ``score_min`` and ``score_max``.
    """
    if extra_info is None:
        extra_info = {}

    capture_details = bool(extra_info.get("capture_details"))
    prompt_extra = extra_info.get("prompt_extra_info")

    result = evaluate_rubric(
        rubric=rubric,
        messages=messages,
        model_info=model_info,
        ground_truth=ground_truth,
        system_message=system_message,
        extra_info=prompt_extra,
        score_min=score_min,
        score_max=score_max,
        return_details=capture_details,
    )

    if capture_details and isinstance(result, dict):
        extra_info["result_details"] = result
        return float(result["score"])

    return float(result)


def _load_messages(messages_path: Path = MESSAGES_PATH) -> Dict[str, Any]:
    with messages_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the reward rubric scorer locally.")
    parser.add_argument(
        "--config",
        type=Path,
        default=CONFIG_PATH,
        help="Path to a reward rubric YAML config file.",
    )
    parser.add_argument(
        "--messages",
        type=Path,
        default=MESSAGES_PATH,
        help="Path to a JSON file containing the conversation messages.",
    )
    parser.add_argument(
        "--no-capture-details",
        action="store_true",
        help="Disable detailed rubric output in the console.",
    )
    args = parser.parse_args()

    config = _load_config(args.config)
    messages_payload: Dict[str, Any] = _load_messages(args.messages)

    messages: List[Dict[str, Any]] = messages_payload["messages"]
    rubric_text: str = config["rubric"]
    score_min: float = float(config.get("score_min", SCORE_MIN))
    score_max: float = float(config.get("score_max", SCORE_MAX))
    ground_truth: Optional[str] = config.get("ground_truth")
    model_info: Dict[str, Any] = dict(config.get("default_model_info", DEFAULT_MODEL_INFO))
    capture_details = not args.no_capture_details
    extra_info: Dict[str, Any] = {"capture_details": capture_details, "prompt_extra_info": None}

    try:
        score_value = score_support_conversation(
            model_info=model_info,
            rubric=rubric_text,
            messages=messages,
            ground_truth=ground_truth,
            system_message=None,
            extra_info=extra_info,
            score_min=score_min,
            score_max=score_max,
        )

        print(f"OpenAI score: {score_value:.2f} (range {score_min}-{score_max})")

        if capture_details:
            result_details = extra_info.get("result_details") or {}
            explanation = result_details.get("explanation", "") if isinstance(result_details, dict) else ""
            if explanation:
                print(f"OpenAI explanation: {explanation}")
    except MissingAPIKeyError as exc:
        print(f"OpenAI example skipped: {exc}")
        raise SystemExit(1)
    except ModelNotFoundError as exc:
        print(f"OpenAI example skipped: {exc.detail}")
        raise SystemExit(1)
    except ProviderRequestError as exc:
        print(f"OpenAI example failed: {exc.detail}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
