import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from eval import codex_eval
from eval.claude_subscription_eval import EvalTarget


def test_codex_judge_config_defaults_to_gpt55() -> None:
    args = argparse.Namespace(
        judge_model="gpt-5.5",
        codex_bin="codex",
        codex_sandbox="read-only",
    )

    config = codex_eval.CodexJudgeConfig.from_args(args)

    assert config == codex_eval.CodexJudgeConfig(
        model="gpt-5.5",
        codex_bin="codex",
        sandbox_mode="read-only",
    )


def test_build_codex_judge_command_ignores_user_config(tmp_path: Path) -> None:
    last_message = tmp_path / "last_message.txt"

    command = codex_eval.build_codex_judge_command(
        codex_bin="codex",
        model="gpt-5.5",
        cwd=tmp_path,
        last_message_file=last_message,
        sandbox_mode="read-only",
    )

    assert command == [
        "codex",
        "--ask-for-approval",
        "never",
        "exec",
        "--model",
        "gpt-5.5",
        "--sandbox",
        "read-only",
        "--ignore-user-config",
        "--cd",
        str(tmp_path),
        "--skip-git-repo-check",
        "--ephemeral",
        "--json",
        "--output-last-message",
        str(last_message),
        "-",
    ]


def test_add_codex_formatting_addendum_marks_the_extra_prompt_text() -> None:
    prompt = codex_eval.add_codex_formatting_addendum("base prompt")

    assert prompt.startswith("base prompt")
    assert "[Codex judge formatting addendum]" in prompt
    assert "Do not run commands." in prompt
    assert "Return only the final JSON object." in prompt


def test_evaluate_log_records_codex_judge_model(tmp_path: Path, monkeypatch) -> None:
    log = tmp_path / "codex" / "gpt-5.5" / "questbench" / "20260601000000" / "log.log"
    log.parent.mkdir(parents=True)
    log.write_text("log", encoding="utf-8")
    prompt_calls: list[dict[str, str]] = []

    def fake_build_judge_prompt(task: str, conclusion: str, collection: str = "papers") -> str:
        prompt_calls.append({"task": task, "conclusion": conclusion, "collection": collection})
        return "judge prompt"

    monkeypatch.setattr(codex_eval, "extract_single_final_thought", lambda path: "agent conclusion")
    monkeypatch.setattr(codex_eval, "build_judge_prompt", fake_build_judge_prompt)
    monkeypatch.setattr(
        codex_eval,
        "run_codex_judge",
        lambda prompt, config: {"precision": 0.8, "recall": 0.6, "f1": 0.685},
    )

    result = codex_eval.evaluate_log(
        tmp_path,
        EvalTarget(
            agent="codex",
            model="gpt-5.5",
            task="questbench",
            timestamp="20260601000000",
            collection="papers_se",
        ),
        codex_eval.CodexJudgeConfig(model="gpt-5.5"),
    )

    assert prompt_calls == [
        {
            "task": "questbench",
            "conclusion": "agent conclusion",
            "collection": "papers_se",
        }
    ]
    assert result["judge_provider"] == "codex"
    assert result["judge_model"] == "gpt-5.5"
    assert result["agent_conclusion"] == "agent conclusion"
    assert result["judgment"] == {"precision": 0.8, "recall": 0.6, "f1": 0.685}
