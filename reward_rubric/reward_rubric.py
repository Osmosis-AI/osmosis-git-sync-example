from __future__ import annotations

import argparse
import copy
import json
import os
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

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


@osmosis_rubric
def score_with_hosted_model(
    solution_str: str,
    ground_truth: str,
    extra_info: Dict[str, Any],
) -> float:
    """
    Delegate rubric scoring to a hosted model while keeping @osmosis_rubric validation.
    """
    if not isinstance(extra_info, dict):
        raise TypeError("extra_info must be a mapping")

    capture_details = bool(extra_info.get("capture_details"))
    prompt_metadata = extra_info.get("metadata")
    model_info = extra_info.get("model_info")
    if not isinstance(model_info, dict):
        raise TypeError("extra_info must include a 'model_info' mapping")

    rubric = extra_info.get("rubric")
    score_min = extra_info.get("score_min")
    score_max = extra_info.get("score_max")

    try:
        result = evaluate_rubric(
            rubric=rubric,
            solution_str=solution_str,
            model_info=model_info,
            ground_truth=ground_truth,
            metadata=prompt_metadata,
            score_min=score_min,
            score_max=score_max,
            return_details=capture_details,
        )
    except MissingAPIKeyError as exc:
        provider_label = str(extra_info.get("provider") or model_info.get("provider") or "").strip()
        provider_hint = f" for provider '{provider_label}'" if provider_label else ""
        api_key_env_value = extra_info.get("api_key_env") or model_info.get("api_key_env")
        if isinstance(api_key_env_value, str) and api_key_env_value.strip():
            api_key_env = api_key_env_value.strip()
        else:
            api_key_env = DEFAULT_PROVIDER_API_KEY_ENV
        raise CLIError(
            f"Missing API key{provider_hint}. Set environment variable '{api_key_env}' or include 'api_key' in the rubric config."
        ) from exc

    if capture_details:
        # Treat extra_info as an input/output channel to surface detailed results.
        extra_info["result_details"] = result
        return float(result["score"])

    return float(result)


def _load_rubric_config(config_path: Path, rubric_id: str) -> RubricConfig:
    parser = RubricConfigParser()
    suite, _ = parser.parse(config_path)
    return suite.get(rubric_id)


def _load_example_record(
    data_path: Path,
    *,
    rubric_id: str,
    conversation_id: Optional[str],
) -> Dict[str, Any]:
    suffix = data_path.suffix.lower()
    if suffix == ".jsonl":
        return _select_record_from_jsonl(
            load_jsonl_records(data_path),
            rubric_id=rubric_id,
            conversation_id=conversation_id,
            source=str(data_path),
        )

    payload = json.loads(data_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Example data must be a JSON object.")
    if "solution_str" not in payload:
        raise ValueError("Example data must include 'solution_str'.")

    record_rubric_id = payload.get("rubric_id")
    if record_rubric_id and record_rubric_id != rubric_id:
        raise CLIError(
            f"Example data in '{data_path}' targets rubric '{record_rubric_id}', "
            f"but rubric '{rubric_id}' was requested."
        )
    if conversation_id:
        record_conversation_id = payload.get("conversation_id")
        if record_conversation_id and record_conversation_id != conversation_id:
            raise CLIError(
                f"Example data in '{data_path}' targets conversation '{record_conversation_id}', "
                f"but conversation '{conversation_id}' was requested."
            )
    return payload


def _select_record_from_jsonl(
    records: Iterable[Dict[str, Any]],
    *,
    rubric_id: str,
    conversation_id: Optional[str],
    source: str,
) -> Dict[str, Any]:
    matched: list[Dict[str, Any]] = []
    for record in records:
        record_rubric = str(record.get("rubric_id") or "").strip()
        if record_rubric and record_rubric != rubric_id:
            continue
        if conversation_id is not None:
            record_conv = str(record.get("conversation_id") or "").strip()
            if record_conv != conversation_id:
                continue
        matched.append(record)

    if conversation_id and not matched:
        raise CLIError(
            f"No conversation '{conversation_id}' found for rubric '{rubric_id}' in '{source}'."
        )
    if not matched:
        raise CLIError(f"No records found for rubric '{rubric_id}' in '{source}'.")

    selected = matched[0]
    if "solution_str" not in selected:
        raise ValueError(
            f"Selected record from '{source}' does not contain 'solution_str'."
        )
    return selected


def _build_extra_info(
    config: RubricConfig,
    record: Dict[str, Any],
    capture_details: bool,
) -> Dict[str, Any]:
    model_info = copy.deepcopy(config.model_info)
    if not isinstance(model_info, dict):
        raise ValueError("Rubric config must include a 'model_info' mapping.")

    provider = str(model_info.get("provider") or "").strip()
    model = str(model_info.get("model") or "").strip()
    if not provider or not model:
        raise ValueError("Model provider and identifier must be set in the config.")

    api_key_env = str(model_info.get("api_key_env") or "").strip()
    if not api_key_env:
        provider_key = provider.lower()
        api_key_env = PROVIDER_API_KEY_ENV.get(provider_key, DEFAULT_PROVIDER_API_KEY_ENV)
        if api_key_env:
            model_info["api_key_env"] = api_key_env

    api_key = model_info.get("api_key") or os.getenv(api_key_env)
    if isinstance(api_key, str) and api_key:
        model_info["api_key"] = api_key

    if config.system_prompt and "system_prompt" not in model_info:
        model_info["system_prompt"] = config.system_prompt

    rubric_text = (config.rubric_text or "").strip()
    if not rubric_text:
        raise ValueError("Rubric config must provide rubric text.")

    extra_info: Dict[str, Any] = {
        "capture_details": capture_details,
        "rubric": rubric_text,
        "score_min": float(config.score_min) if config.score_min is not None else SCORE_MIN,
        "score_max": float(config.score_max) if config.score_max is not None else SCORE_MAX,
        "model_info": model_info,
        "rubric_source": config.source_label,
        # The hosted scoring service expects these top-level identifiers.
        "provider": provider,
        "model": model,
    }

    api_key_env_value = model_info.get("api_key_env")
    if isinstance(api_key_env_value, str) and api_key_env_value.strip():
        extra_info["api_key_env"] = api_key_env_value.strip()

    api_key_value = model_info.get("api_key")
    if isinstance(api_key_value, str) and api_key_value:
        extra_info["api_key"] = api_key_value

    metadata = record.get("metadata")
    if isinstance(metadata, dict):
        extra_info["metadata"] = metadata

    conversation_id = record.get("conversation_id")
    if isinstance(conversation_id, str):
        extra_info["conversation_id"] = conversation_id.strip()

    return extra_info


def run_example(
    *,
    config_path: Path = DEFAULT_CONFIG_PATH,
    data_path: Path = DEFAULT_DATA_PATH,
    rubric_id: str = DEFAULT_RUBRIC_ID,
    conversation_id: Optional[str] = None,
    capture_details: bool = True,
) -> tuple[float, Dict[str, Any]]:
    config = _load_rubric_config(config_path, rubric_id)
    record = _load_example_record(
        data_path,
        rubric_id=rubric_id,
        conversation_id=conversation_id,
    )

    extra_info = _build_extra_info(config, record, capture_details)
    ground_truth = str(record.get("ground_truth") or config.ground_truth or "").strip()
    if not ground_truth:
        raise ValueError("Ground truth must be provided by the config or the data record.")

    solution_str = str(record.get("solution_str") or "").strip()
    if not solution_str:
        raise ValueError("Solution string must be provided by the data record.")

    original_input = record.get("original_input")
    if isinstance(original_input, str):
        extra_info["original_input"] = original_input.strip()

    score = score_with_hosted_model(
        solution_str=solution_str,
        ground_truth=ground_truth,
        extra_info=extra_info,
    )

    return score, extra_info


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the reward rubric scorer example.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH, help="Reward rubric YAML config.")
    parser.add_argument(
        "--data",
        type=Path,
        default=DEFAULT_DATA_PATH,
        help="JSON or JSONL file with example inputs.",
    )
    parser.add_argument("--rubric", default=DEFAULT_RUBRIC_ID, help="Rubric identifier to evaluate.")
    parser.add_argument(
        "--conversation",
        help="Conversation ID to select when loading JSONL datasets (defaults to the first matching record).",
    )
    parser.add_argument("--no-details", action="store_true", help="Disable detailed hosted-model output.")
    args = parser.parse_args()

    capture_details = not args.no_details

    try:
        score_value, extra_info = run_example(
            config_path=args.config,
            data_path=args.data,
            rubric_id=args.rubric,
            conversation_id=args.conversation,
            capture_details=capture_details,
        )
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

    if capture_details:
        details = extra_info.get("result_details") or {}
        if isinstance(details, dict):
            explanation = details.get("explanation")
            if isinstance(explanation, str) and explanation.strip():
                print(f"Explanation: {explanation.strip()}")


score_support_conversation = score_with_hosted_model


if __name__ == "__main__":
    main()
