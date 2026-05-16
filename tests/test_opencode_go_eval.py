import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from eval import opencode_go_eval
from eval.claude_subscription_eval import EvalTarget


def test_opencode_go_judge_config_defaults_to_qwen36_plus() -> None:
    args = argparse.Namespace(judge_model="qwen3.6-plus", repair_model="")

    config = opencode_go_eval.OpenCodeGoJudgeConfig.from_args(args)

    assert config == opencode_go_eval.OpenCodeGoJudgeConfig(
        model="qwen3.6-plus",
        repair_model="qwen3.6-plus",
    )


def test_run_opencode_go_judge_uses_opencode_provider(monkeypatch) -> None:
    calls: list[dict[str, object]] = []

    class FakeInference:
        def __init__(self, provider: str, model_name: str) -> None:
            calls.append({"provider": provider, "model_name": model_name})

        def generate(self, prompt: str, max_tokens: int, temperature: float, **kwargs: object) -> dict[str, object]:
            calls.append({"prompt": prompt, "max_tokens": max_tokens, "temperature": temperature, **kwargs})
            return {"content": '{"precision": 1.0, "recall": 0.5, "f1": 0.667}'}

    monkeypatch.setattr(opencode_go_eval, "LLMInference", FakeInference)

    result = opencode_go_eval.run_opencode_go_judge("judge prompt", opencode_go_eval.OpenCodeGoJudgeConfig())

    assert calls == [
        {"provider": "opencode_go", "model_name": "qwen3.6-plus"},
        {
            "prompt": "judge prompt",
            "max_tokens": 4096,
            "temperature": 0,
        },
    ]
    assert result == {"precision": 1.0, "recall": 0.5, "f1": 0.667}


def test_run_opencode_go_judge_uses_repair_model_for_non_json_output(monkeypatch) -> None:
    calls: list[dict[str, object]] = []

    class FakeInference:
        def __init__(self, provider: str, model_name: str) -> None:
            calls.append({"provider": provider, "model_name": model_name})
            self.model_name = model_name

        def generate(self, prompt: str, max_tokens: int, temperature: float, **kwargs: object) -> dict[str, object]:
            calls.append({"model_name": self.model_name, "prompt": prompt, "max_tokens": max_tokens})
            if self.model_name == "deepseek-v4-flash":
                return {"content": "not json"}
            return {"content": '{"precision": 0.7, "recall": 0.8, "f1": 0.747}'}

    monkeypatch.setattr(opencode_go_eval, "LLMInference", FakeInference)

    result = opencode_go_eval.run_opencode_go_judge(
        "judge prompt",
        opencode_go_eval.OpenCodeGoJudgeConfig(
            model="deepseek-v4-flash",
            repair_model="qwen3.6-plus",
        ),
    )

    assert calls[0] == {"provider": "opencode_go", "model_name": "deepseek-v4-flash"}
    assert calls[2] == {"provider": "opencode_go", "model_name": "qwen3.6-plus"}
    assert result == {"precision": 0.7, "recall": 0.8, "f1": 0.747}


def test_add_opencode_go_formatting_addendum_marks_the_extra_prompt_text() -> None:
    prompt = opencode_go_eval.add_opencode_go_formatting_addendum("base prompt")

    assert prompt.startswith("base prompt")
    assert "[OpenCode Go formatting addendum]" in prompt
    assert "Return only the final JSON object." in prompt
    assert "[/OpenCode Go formatting addendum]" in prompt


def test_evaluate_log_records_opencode_go_judge_model(tmp_path: Path, monkeypatch) -> None:
    log = tmp_path / "claude" / "sonnet" / "questbench" / "20260511000000" / "log.log"
    log.parent.mkdir(parents=True)
    log.write_text("log", encoding="utf-8")

    monkeypatch.setattr(opencode_go_eval, "extract_single_final_thought", lambda path: "agent conclusion")
    monkeypatch.setattr(opencode_go_eval, "build_judge_prompt", lambda task, conclusion: "judge prompt")
    monkeypatch.setattr(
        opencode_go_eval,
        "run_opencode_go_judge",
        lambda prompt, config: {"precision": 0.8, "recall": 0.6, "f1": 0.685},
    )

    result = opencode_go_eval.evaluate_log(
        tmp_path,
        EvalTarget(agent="claude", model="sonnet", task="questbench", timestamp="20260511000000"),
        opencode_go_eval.OpenCodeGoJudgeConfig(model="qwen3.6-plus"),
    )

    assert result["judge_provider"] == "opencode_go"
    assert result["judge_model"] == "qwen3.6-plus"
    assert result["repair_model"] == "qwen3.6-plus"
    assert result["agent_conclusion"] == "agent conclusion"
    assert result["judgment"] == {"precision": 0.8, "recall": 0.6, "f1": 0.685}


def test_default_output_path_groups_results_by_evaluated_model_and_judge_model() -> None:
    target = EvalTarget(
        agent="opencode_go",
        model="deepseek-v4-pro",
        task="awareness_detection",
        timestamp="20260514150955_70000",
    )
    config = opencode_go_eval.OpenCodeGoJudgeConfig(model="qwen3.6-plus")

    path = opencode_go_eval.default_output_path(target, config)

    assert path == Path("results/deepseek-v4-pro/qwen3.6-plus/awareness_detection.json")


def test_write_result_once_refuses_to_overwrite_existing_results(tmp_path: Path) -> None:
    output = tmp_path / "results" / "opencode_go" / "deepseek-v4-pro" / "judge.json"
    output.parent.mkdir(parents=True)
    output.write_text('{"old": true}\n', encoding="utf-8")

    try:
        opencode_go_eval.write_result_once(output, {"new": True}, overwrite=False)
    except FileExistsError as error:
        assert "Refusing to overwrite existing result" in str(error)
    else:
        raise AssertionError("Expected FileExistsError")

    assert output.read_text(encoding="utf-8") == '{"old": true}\n'


def test_write_result_once_allows_explicit_overwrite(tmp_path: Path) -> None:
    output = tmp_path / "result.json"
    output.write_text('{"old": true}\n', encoding="utf-8")

    opencode_go_eval.write_result_once(output, {"new": True}, overwrite=True)

    assert output.read_text(encoding="utf-8") == '{\n  "new": true\n}\n'
