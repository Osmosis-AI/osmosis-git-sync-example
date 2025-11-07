from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Iterable

from osmosis_ai import evaluate_rubric, osmosis_rubric
from osmosis_ai.cli_services import CLIError, load_rubric_suite
from osmosis_ai.cli_services.dataset import DatasetLoader
from osmosis_ai.rubric_eval import DEFAULT_API_KEY_ENV as PROVIDER_API_KEY_ENV
from osmosis_ai.rubric_types import MissingAPIKeyError

SCORE_MIN = 0.0
SCORE_MAX = 1.0
DEFAULT_PROVIDER_API_KEY_ENV = "OPENAI_API_KEY"

DEFAULT_CONFIG_PATH = Path(__file__).with_name("reward_rubric_config.yaml")
DEFAULT_DATA_PATH = Path(__file__).with_name("sample_data.jsonl")
DEFAULT_RUBRIC_ID = "support_followup"

@osmosis_rubric
def score_support_conversation(
    solution_str: str,
    ground_truth: str,
    extra_info: Dict[str, Any] | None,
    *,
    _context: Dict[str, Any] | None = None,
) -> float:
    context = _context or _default_context()
    try:
        result = evaluate_rubric(
            rubric=context["rubric"],
            solution_str=solution_str,
            model_info=context["model_info"],
            ground_truth=ground_truth,
            metadata=None,
            score_min=context["score_min"],
            score_max=context["score_max"],
            return_details=False,
        )
    except MissingAPIKeyError as exc:
        provider = context["model_info"]["provider"]
        api_key_env = context["model_info"]["api_key_env"]
        raise CLIError(
            f"Missing API key for provider '{provider}'. "
            f"Set '{api_key_env}' or add an explicit 'api_key' in reward_rubric_config.yaml."
        ) from exc

    return float(result)

def _clean_text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _load_context(
    config_path: Path = DEFAULT_CONFIG_PATH,
    rubric_id: str = DEFAULT_RUBRIC_ID,
) -> Dict[str, Any]:
    suite = load_rubric_suite(config_path)
    config = suite.get(rubric_id)

    rubric_text = _clean_text(config.rubric_text)

    model_info = dict(config.model_info or {})
    provider = _clean_text(model_info.get("provider")) or "openai"
    model_name = _clean_text(model_info.get("model")) or "gpt-5-mini"

    api_key_env = (
        model_info.get("api_key_env")
        or PROVIDER_API_KEY_ENV.get(provider.lower())
        or DEFAULT_PROVIDER_API_KEY_ENV
    )
    model_info.update(
        {
            "provider": provider,
            "model": model_name,
            "api_key_env": api_key_env,
            "api_key": model_info.get("api_key") or os.getenv(api_key_env),
        }
    )

    score_min = float(config.score_min) if config.score_min is not None else SCORE_MIN
    score_max = float(config.score_max) if config.score_max is not None else SCORE_MAX

    return {
        "rubric_id": rubric_id,
        "rubric": rubric_text,
        "ground_truth": _clean_text(config.ground_truth),
        "model_info": model_info,
        "score_min": score_min,
        "score_max": score_max,
    }


def _default_context() -> Dict[str, Any]:
    return _load_context()


def _pick_record(
    records: Iterable[Any],
    data_path: Path,
    conversation_id: str | None,
) -> Any:
    records = list(records)
    if not records:
        raise CLIError(f"No records found in '{data_path}'.")

    if conversation_id:
        target = _clean_text(conversation_id)
        for record in records:
            record_id = _clean_text(getattr(record, "conversation_id", None))
            if record_id == target:
                return record
        raise CLIError(
            f"Conversation '{conversation_id}' was not found in '{data_path}'. "
            "Omit the conversation id to use the first sample instead."
        )

    return records[0]




def run_example(
    *,
    config_path: Path = DEFAULT_CONFIG_PATH,
    data_path: Path = DEFAULT_DATA_PATH,
    rubric_id: str = DEFAULT_RUBRIC_ID,
    conversation_id: str | None = None,
) -> tuple[float, Dict[str, Any]]:
    context = _load_context(config_path, rubric_id)
    loader = DatasetLoader()
    records = loader.load(data_path)
    record = _pick_record(records, data_path, conversation_id)

    solution_str = _clean_text(getattr(record, "solution_str", None))
    ground_truth = _clean_text(getattr(record, "ground_truth", None)) or context["ground_truth"]

    score = score_support_conversation(
        solution_str=solution_str,
        ground_truth=ground_truth,
        extra_info={},
        _context=context,
    )
    return score, context


def main() -> None:
    try:
        score_value, context = run_example()
    except (CLIError, OSError, ValueError, TypeError) as exc:
        print(f"Reward rubric example failed: {exc}")
        raise SystemExit(1) from exc

    provider = context["model_info"]["provider"]
    model = context["model_info"]["model"]
    score_min = context["score_min"]
    score_max = context["score_max"]
    print(f"{provider} {model} score: {score_value:.2f} (range {score_min}-{score_max})")


if __name__ == "__main__":
    main()
