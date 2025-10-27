from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict

from osmosis_ai import evaluate_rubric, osmosis_rubric
from osmosis_ai.cli_services import CLIError, RubricConfig, load_rubric_suite
from osmosis_ai.cli_services.dataset import DatasetLoader, DatasetRecord
from osmosis_ai.rubric_eval import DEFAULT_API_KEY_ENV as PROVIDER_API_KEY_ENV
from osmosis_ai.rubric_types import MissingAPIKeyError

SCORE_MIN = 0.0
SCORE_MAX = 1.0
DEFAULT_PROVIDER_API_KEY_ENV = "OPENAI_API_KEY"

DEFAULT_CONFIG_PATH = Path(__file__).with_name("reward_rubric_config.yaml")
DEFAULT_DATA_PATH = Path(__file__).with_name("sample_data.jsonl")
DEFAULT_RUBRIC_ID = "support_followup"


def _normalize_text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


@osmosis_rubric
def score_support_conversation(
    solution_str: str,
    ground_truth: str,
    extra_info: Dict[str, Any],
) -> float:
    """Delegate rubric scoring to a hosted model while keeping @osmosis_rubric validation."""
    extra = extra_info or {}
    required_keys = ["rubric", "provider", "model", "api_key", "api_key_env", "score_min", "score_max"]
    for key in required_keys:
        if key not in extra:
            raise CLIError(f"Missing required key '{key}' in extra_info.")
    provider = extra.get("provider")
    model_name = extra.get("model")
    api_key = extra.get("api_key")
    api_key_env = extra.get("api_key_env") or DEFAULT_PROVIDER_API_KEY_ENV
    model_settings = dict(extra.get("model_settings") or {})
    capture_details = bool(extra.get("capture_details"))

    model_info = dict(model_settings)
    model_info["provider"] = provider
    model_info["model"] = model_name
    model_info["api_key"] = api_key
    model_info["api_key_env"] = api_key_env

    try:
        result = evaluate_rubric(
            rubric=extra.get("rubric"),
            solution_str=solution_str,
            model_info=model_info,
            ground_truth=ground_truth,
            metadata=extra.get("metadata"),
            score_min=extra.get("score_min"),
            score_max=extra.get("score_max"),
            return_details=capture_details,
        )
    except MissingAPIKeyError as exc:
        provider_label = provider or "provider"
        raise CLIError(
            f"Missing API key for provider '{provider_label}'. "
            f"Set environment variable '{api_key_env}' or include 'api_key' in the rubric config."
        ) from exc

    if capture_details:
        extra["result_details"] = result
        return float(result["score"])

    return float(result)


def _build_extra_info(
    config: RubricConfig,
    record: DatasetRecord,
    capture_details: bool,
) -> Dict[str, Any]:
    model_info = config.model_info or {}
    provider = model_info.get("provider")
    model_name = model_info.get("model")
    api_key = model_info.get("api_key")
    api_key_env = model_info.get("api_key_env")

    if not api_key_env and provider:
        api_key_env = PROVIDER_API_KEY_ENV.get(provider.lower())
    api_key_env = api_key_env or DEFAULT_PROVIDER_API_KEY_ENV

    api_key_value = api_key or os.getenv(api_key_env)

    extra: Dict[str, Any] = {
        "capture_details": capture_details,
        "rubric": config.rubric_text,
        "provider": provider,
        "model": model_name,
        "api_key": api_key_value,
        "api_key_env": api_key_env,
        "score_min": float(config.score_min) if config.score_min is not None else SCORE_MIN,
        "score_max": float(config.score_max) if config.score_max is not None else SCORE_MAX,
    }

    original_input = record.original_input or config.original_input
    if original_input and "original_input" not in extra:
        extra["original_input"] = original_input

    if record.metadata and "metadata" not in extra:
        extra["metadata"] = record.metadata

    return extra


def run_example(
    *,
    config_path: Path = DEFAULT_CONFIG_PATH,
    data_path: Path = DEFAULT_DATA_PATH,
    rubric_id: str = DEFAULT_RUBRIC_ID,
    conversation_id: str | None = None,
    capture_details: bool = True,
) -> tuple[float, Dict[str, Any]]:
    suite = load_rubric_suite(config_path)
    config = suite.get(rubric_id)
    loader = DatasetLoader()
    suffix = data_path.suffix.lower()
    normalized_rubric = rubric_id.strip()
    normalized_conversation = conversation_id.strip() if conversation_id else ""

    if suffix != ".jsonl":
        raise CLIError(f"Unsupported data file '{data_path}'. Provide a JSONL dataset.")

    records = loader.load(data_path)

    matching_records = []
    for record in records:
        record_rubric = record.rubric_id.strip() if isinstance(record.rubric_id, str) else ""
        if normalized_rubric and record_rubric and record_rubric != normalized_rubric:
            continue
        record_conversation = record.conversation_id.strip() if isinstance(record.conversation_id, str) else ""
        if normalized_conversation and record_conversation != normalized_conversation:
            continue
        matching_records.append(record)

    if normalized_conversation and not matching_records:
        raise CLIError(
            f"No conversation '{conversation_id}' found for rubric '{rubric_id}' in '{data_path}'."
        )
    if not matching_records:
        raise CLIError(f"No records found for rubric '{rubric_id}' in '{data_path}'.")

    record = matching_records[0]

    extra_info = _build_extra_info(config, record, capture_details)

    ground_truth = _normalize_text(record.ground_truth or config.ground_truth)
    if not ground_truth:
        raise CLIError("Ground truth cannot be empty after normalization.")
    solution_str = _normalize_text(record.solution_str)
    if not solution_str:
        raise CLIError("Solution string cannot be empty after normalization.")

    score = score_support_conversation(
        solution_str=solution_str,
        ground_truth=ground_truth,
        extra_info=extra_info,
    )

    return score, extra_info


def main() -> None:
    try:
        score_value, extra_info = run_example()
    except (CLIError, OSError, ValueError, TypeError) as exc:
        print(f"Reward rubric example failed: {exc}")
        raise SystemExit(1) from exc

    provider_label = extra_info.get("provider", "provider")
    model_label = extra_info.get("model")
    score_min = extra_info.get("score_min", SCORE_MIN)
    score_max = extra_info.get("score_max", SCORE_MAX)
    model_suffix = f" {model_label}" if model_label else ""
    print(f"{provider_label}{model_suffix} score: {score_value:.2f} (range {score_min}-{score_max})")

    details = extra_info.get("result_details") or {}
    if isinstance(details, dict):
        explanation = details.get("explanation")
        if isinstance(explanation, str) and explanation.strip():
            print(f"Explanation: {explanation.strip()}")

if __name__ == "__main__":
    main()
