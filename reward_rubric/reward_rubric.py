from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict

from osmosis_ai import evaluate_rubric, osmosis_rubric
from osmosis_ai.cli_services import (
    CLIError,
    RubricConfig,
    RubricConfigParser,
    load_jsonl_records,
)
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
def score_with_hosted_model(
    solution_str: str,
    ground_truth: str,
    extra_info: Dict[str, Any],
) -> float:
    """Delegate rubric scoring to a hosted model while keeping @osmosis_rubric validation."""
    if not isinstance(extra_info, dict):
        raise TypeError("extra_info must be a mapping")

    capture_details = bool(extra_info.get("capture_details"))
    model_info = extra_info.get("model_info")
    if not isinstance(model_info, dict):
        raise TypeError("extra_info must include a 'model_info' mapping")

    try:
        result = evaluate_rubric(
            rubric=extra_info.get("rubric"),
            solution_str=solution_str,
            model_info=model_info,
            ground_truth=ground_truth,
            metadata=extra_info.get("metadata"),
            score_min=extra_info.get("score_min"),
            score_max=extra_info.get("score_max"),
            return_details=capture_details,
        )
    except MissingAPIKeyError as exc:
        provider_label = _normalize_text(extra_info.get("provider") or model_info.get("provider") or "")
        provider_hint = f" for provider '{provider_label}'" if provider_label else ""
        api_key_env = _normalize_text(extra_info.get("api_key_env") or model_info.get("api_key_env")) or DEFAULT_PROVIDER_API_KEY_ENV
        raise CLIError(
            f"Missing API key{provider_hint}. Set environment variable '{api_key_env}' or include 'api_key' in the rubric config."
        ) from exc

    if capture_details:
        extra_info["result_details"] = result
        return float(result["score"])

    return float(result)


def _load_example_record(
    data_path: Path,
    *,
    rubric_id: str,
    conversation_id: str | None,
) -> Dict[str, Any]:
    suffix = data_path.suffix.lower()
    if suffix == ".jsonl":
        for entry in load_jsonl_records(data_path):
            record_rubric = _normalize_text(entry.get("rubric_id"))
            if record_rubric and record_rubric != rubric_id:
                continue
            if conversation_id:
                record_conv = _normalize_text(entry.get("conversation_id"))
                if record_conv and record_conv != conversation_id:
                    continue
            return entry
        if conversation_id:
            raise CLIError(
                f"No conversation '{conversation_id}' found for rubric '{rubric_id}' in '{data_path}'."
            )
        raise CLIError(f"No records found for rubric '{rubric_id}' in '{data_path}'.")

    payload = json.loads(data_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Example data must be a JSON object.")
    return payload


def _build_extra_info(
    config: RubricConfig,
    record: Dict[str, Any],
    capture_details: bool,
) -> Dict[str, Any]:
    model_info = dict(config.model_info or {})

    provider = _normalize_text(model_info.get("provider"))
    model = _normalize_text(model_info.get("model"))

    api_key_env = _normalize_text(model_info.get("api_key_env")) or PROVIDER_API_KEY_ENV.get(
        provider.lower(), DEFAULT_PROVIDER_API_KEY_ENV
    )
    if api_key_env:
        model_info["api_key_env"] = api_key_env

    api_key = _normalize_text(model_info.get("api_key") or os.getenv(api_key_env))
    if api_key:
        model_info["api_key"] = api_key

    if config.system_prompt and "system_prompt" not in model_info:
        model_info["system_prompt"] = config.system_prompt

    extra_info: Dict[str, Any] = {
        "capture_details": capture_details,
        "rubric": config.rubric_text or "",
        "score_min": float(config.score_min) if config.score_min is not None else SCORE_MIN,
        "score_max": float(config.score_max) if config.score_max is not None else SCORE_MAX,
        "model_info": model_info,
        "rubric_source": config.source_label,
        "provider": provider,
        "model": model,
    }

    if api_key_env:
        extra_info["api_key_env"] = api_key_env
    if api_key:
        extra_info["api_key"] = api_key

    metadata = record.get("metadata")
    if isinstance(metadata, dict):
        extra_info["metadata"] = metadata

    for key in ("conversation_id", "original_input"):
        value = _normalize_text(record.get(key))
        if value:
            extra_info[key] = value

    return extra_info


def run_example(
    *,
    config_path: Path = DEFAULT_CONFIG_PATH,
    data_path: Path = DEFAULT_DATA_PATH,
    rubric_id: str = DEFAULT_RUBRIC_ID,
    conversation_id: str | None = None,
    capture_details: bool = True,
) -> tuple[float, Dict[str, Any]]:
    suite, _ = RubricConfigParser().parse(config_path)
    config = suite.get(rubric_id)
    record = _load_example_record(
        data_path,
        rubric_id=rubric_id,
        conversation_id=conversation_id,
    )

    extra_info = _build_extra_info(config, record, capture_details)

    ground_truth = _normalize_text(record.get("ground_truth")) or _normalize_text(config.ground_truth)
    solution_str = _normalize_text(record.get("solution_str"))

    score = score_with_hosted_model(
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

    model_info = extra_info.get("model_info", {})
    provider_label = model_info.get("provider", "provider")
    model_label = model_info.get("model")
    score_min = extra_info.get("score_min", SCORE_MIN)
    score_max = extra_info.get("score_max", SCORE_MAX)
    model_suffix = f" {model_label}" if model_label else ""
    print(f"{provider_label}{model_suffix} score: {score_value:.2f} (range {score_min}-{score_max})")

    conversation_label = extra_info.get("conversation_id")
    if isinstance(conversation_label, str) and conversation_label.strip():
        print(f"Conversation: {conversation_label.strip()}")

    details = extra_info.get("result_details") or {}
    if isinstance(details, dict):
        explanation = details.get("explanation")
        if isinstance(explanation, str) and explanation.strip():
            print(f"Explanation: {explanation.strip()}")


score_support_conversation = score_with_hosted_model


if __name__ == "__main__":
    main()
