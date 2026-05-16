import argparse
import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from eval.claude_subscription_eval import (
    EvalTarget,
    build_judge_prompt,
    extract_json_object,
    log_path,
)


def test_log_path_points_to_fire_bench_log_location() -> None:
    target = EvalTarget(agent="claude", model="sonnet", task="llm_value_consistency", timestamp="20260508135739")

    path = log_path(Path("log"), target)

    assert path == Path("log/claude/sonnet/llm_value_consistency/20260508135739/log.log")


def test_eval_target_is_created_from_cli_arguments() -> None:
    args = argparse.Namespace(
        agent="claude",
        model="claude-sonnet-4-20250514",
        task="llm_value_consistency",
        timestamp="20260508135739",
    )

    target = EvalTarget.from_args(args)

    assert target == EvalTarget(
        agent="claude",
        model="claude-sonnet-4-20250514",
        task="llm_value_consistency",
        timestamp="20260508135739",
    )


def test_build_judge_prompt_includes_task_ground_truth_and_agent_conclusion() -> None:
    prompt = build_judge_prompt("llm_value_consistency", "agent conclusion text")

    assert "Do large language models exhibit the same value structure as humans" in prompt
    assert "Different large language models do not consistently exhibit" in prompt
    assert "agent conclusion text" in prompt
    assert "Precision = true_positive_response_claims / total_response_claims" in prompt


def test_build_judge_prompt_rejects_unknown_tasks() -> None:
    with pytest.raises(ValueError, match="Unknown task query"):
        build_judge_prompt("unknown_task", "agent conclusion text")


def test_extract_json_object_accepts_plain_json() -> None:
    parsed = extract_json_object('{"precision": 0.5, "recall": 0.25, "f1": 0.333}')

    assert parsed == {"precision": 0.5, "recall": 0.25, "f1": 0.333}


def test_extract_json_object_accepts_markdown_fenced_json() -> None:
    output = """```json
{"precision": 0.0, "recall": 0.0, "f1": 0.0}
```"""

    parsed = extract_json_object(output)

    assert parsed == {"precision": 0.0, "recall": 0.0, "f1": 0.0}


def test_extract_json_object_rejects_invalid_json() -> None:
    with pytest.raises(ValueError, match="valid JSON"):
        extract_json_object("not json")
