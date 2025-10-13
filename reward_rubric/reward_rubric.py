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
    """
    Delegate rubric scoring to a hosted model while keeping @osmosis_rubric validation.
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
        result = evaluate_rubric(
            rubric=rubric_text,
            messages=messages,
            model_info=model_info,
            ground_truth=ground_truth,
            system_message=None,
            extra_info=extra_info.get("prompt_extra_info"),
            score_min=score_min,
            score_max=score_max,
            return_details=capture_details,
        )
    except MissingAPIKeyError as exc:
        print(f"OpenAI example skipped: {exc}")
        raise SystemExit(1)
    except ModelNotFoundError as exc:
        print(f"OpenAI example skipped: {exc.detail}")
        raise SystemExit(1)
    except ProviderRequestError as exc:
        print(f"OpenAI example failed: {exc.detail}")
        raise SystemExit(1)
    else:
        score_value = float(result["score"]) if isinstance(result, dict) else float(result)
        explanation = result.get("explanation", "") if isinstance(result, dict) else ""

        print(f"OpenAI score: {score_value:.2f} (range {score_min}-{score_max})")
        if capture_details and explanation:
            print(f"OpenAI explanation: {explanation}")


if __name__ == "__main__":
    main()
