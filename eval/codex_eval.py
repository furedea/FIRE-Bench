from __future__ import annotations

import argparse
import importlib.util
import subprocess
import sys
import tempfile
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Self

ROOT_DIR = Path(__file__).resolve().parents[1]


def _load_claude_eval_module() -> Any:
    module_path = Path(__file__).parent / "claude_subscription_eval.py"
    spec = importlib.util.spec_from_file_location("firebench_claude_subscription_eval", module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load Claude subscription eval helpers from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


claude_eval = _load_claude_eval_module()
EvalTarget = claude_eval.EvalTarget
build_judge_prompt = claude_eval.build_judge_prompt
extract_json_object = claude_eval.extract_json_object
extract_single_final_thought = claude_eval.extract_single_final_thought
log_path = claude_eval.log_path
write_result = claude_eval.write_result

CODEX_FORMATTING_ADDENDUM = """\
[Codex judge formatting addendum]
Return only the final JSON object.
Do not run commands.
Do not include reasoning, analysis, preamble, markdown fences, or commentary.
The first character of your response must be "{".
The last character of your response must be "}".
[/Codex judge formatting addendum]
"""


@dataclass(frozen=True, slots=True)
class CodexJudgeConfig:
    model: str = "gpt-5.5"
    codex_bin: str = "codex"
    sandbox_mode: str = "read-only"

    @classmethod
    def from_args(cls, args: argparse.Namespace) -> Self:
        return cls(
            model=args.judge_model,
            codex_bin=args.codex_bin,
            sandbox_mode=args.codex_sandbox,
        )


def add_codex_formatting_addendum(prompt: str) -> str:
    return f"{prompt}\n\n{CODEX_FORMATTING_ADDENDUM}"


def build_codex_judge_command(
    *,
    codex_bin: str,
    model: str,
    cwd: Path,
    last_message_file: Path,
    sandbox_mode: str,
) -> list[str]:
    return [
        codex_bin,
        "--ask-for-approval",
        "never",
        "exec",
        "--model",
        model,
        "--sandbox",
        sandbox_mode,
        "--ignore-user-config",
        "--cd",
        str(cwd),
        "--skip-git-repo-check",
        "--ephemeral",
        "--json",
        "--output-last-message",
        str(last_message_file),
        "-",
    ]


def run_codex_judge(prompt: str, config: CodexJudgeConfig) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="firebench_codex_judge_") as temp_dir:
        last_message_file = Path(temp_dir) / "last_message.txt"
        command = build_codex_judge_command(
            codex_bin=config.codex_bin,
            model=config.model,
            cwd=ROOT_DIR,
            last_message_file=last_message_file,
            sandbox_mode=config.sandbox_mode,
        )
        process = subprocess.run(
            command,
            cwd=ROOT_DIR,
            input=prompt,
            capture_output=True,
            text=True,
        )
        if process.returncode != 0:
            raise RuntimeError(
                "Codex judge failed with exit code "
                f"{process.returncode}\nstdout:\n{process.stdout}\nstderr:\n{process.stderr}"
            )
        if not last_message_file.exists():
            raise RuntimeError("Codex judge did not write a final message")
        return extract_json_object(last_message_file.read_text(encoding="utf-8"))


def evaluate_log(base_dir: Path, target: EvalTarget, config: CodexJudgeConfig) -> dict[str, Any]:
    path = log_path(base_dir, target)
    if not path.exists():
        raise FileNotFoundError(f"Log file not found: {path}")

    agent_conclusion = extract_single_final_thought(path)
    if not agent_conclusion:
        raise ValueError(f"Could not extract final conclusion from: {path}")

    prompt = add_codex_formatting_addendum(build_judge_prompt(target.task, agent_conclusion, target.collection))
    judgment = run_codex_judge(prompt, config)
    return {
        "agent": target.agent,
        "model": target.model,
        "collection": target.collection,
        "task": target.task,
        "timestamp": target.timestamp,
        "judge_provider": "codex",
        "judge_model": config.model,
        "log_path": str(path),
        "agent_conclusion": agent_conclusion,
        "judgment": judgment,
    }


def default_output_path(target: EvalTarget, config: CodexJudgeConfig) -> Path:
    return Path("results") / target.model / config.model / f"{target.task}.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate one FIRE-Bench log with Codex.")
    parser.add_argument("--agent", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--task", required=True)
    parser.add_argument("--timestamp", required=True)
    parser.add_argument("--collection", default=claude_eval.DEFAULT_COLLECTION)
    parser.add_argument("--base-dir", default="log")
    parser.add_argument("--judge-model", default="gpt-5.5")
    parser.add_argument("--codex-bin", default="codex")
    parser.add_argument("--codex-sandbox", default="read-only")
    parser.add_argument("--output", default="")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    target = EvalTarget.from_args(args)
    config = CodexJudgeConfig.from_args(args)
    result = evaluate_log(Path(args.base_dir), target, config)

    output_path = Path(args.output) if args.output else default_output_path(target, config)
    write_result(output_path, result)

    judgment = result["judgment"]
    print(
        textwrap.dedent(
            f"""\
            Codex evaluation complete.
            Output: {output_path}
            Judge model: {config.model}
            Precision: {judgment.get("precision")}
            Recall: {judgment.get("recall")}
            F1: {judgment.get("f1")}
            Summary: {judgment.get("summary")}
            """
        ).strip()
    )


if __name__ == "__main__":
    main()
