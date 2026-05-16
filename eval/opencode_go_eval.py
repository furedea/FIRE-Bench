from __future__ import annotations

import argparse
import importlib.util
import sys
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Self

ROOT_DIR = Path(__file__).resolve().parents[1]
RAGCHECKER_DIR = Path(__file__).parent / "RAGChecker"
sys.path.append(str(RAGCHECKER_DIR))

from utils import extract_single_final_thought  # noqa: E402


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
log_path = claude_eval.log_path
write_result = claude_eval.write_result


def _load_llm_inference_class() -> type:
    module_path = ROOT_DIR / "utils" / "llm_inference.py"
    spec = importlib.util.spec_from_file_location("firebench_llm_inference", module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load LLMInference from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module.LLMInference


LLMInference = _load_llm_inference_class()

OPENCODE_GO_FORMATTING_ADDENDUM = """\
[OpenCode Go formatting addendum]
Return only the final JSON object.
Do not include reasoning, analysis, preamble, markdown fences, or commentary.
The first character of your response must be "{".
The last character of your response must be "}".
[/OpenCode Go formatting addendum]
"""


@dataclass(frozen=True, slots=True)
class OpenCodeGoJudgeConfig:
    model: str = "qwen3.6-plus"
    repair_model: str = "qwen3.6-plus"

    @classmethod
    def from_args(cls, args: argparse.Namespace) -> Self:
        repair_model = args.repair_model or args.judge_model
        return cls(model=args.judge_model, repair_model=repair_model)


def add_opencode_go_formatting_addendum(prompt: str) -> str:
    return f"{prompt}\n\n{OPENCODE_GO_FORMATTING_ADDENDUM}"


def run_opencode_go_judge(prompt: str, config: OpenCodeGoJudgeConfig) -> dict[str, Any]:
    inference = LLMInference(provider="opencode_go", model_name=config.model)
    response = inference.generate(prompt, max_tokens=4096, temperature=0)
    content = response.get("content", "")
    if not isinstance(content, str):
        raise ValueError(f"OpenCode Go judge returned non-string content: {content}")
    if not content.strip():
        return empty_judgment(config.model)
    try:
        return extract_json_object(content)
    except ValueError:
        return repair_judge_output(config, content)


def repair_judge_output(config: OpenCodeGoJudgeConfig, non_json_output: str) -> dict[str, Any]:
    inference = LLMInference(provider="opencode_go", model_name=config.repair_model)
    repair_prompt = f"""\
Convert the following judge output into valid JSON matching the requested FIRE-Bench evaluation schema.
Do not add new evidence. Use only the claims and judgments already present in the text.
Return only the JSON object.

Judge output:
{non_json_output[:12000]}
"""
    response = inference.generate(repair_prompt, max_tokens=4096, temperature=0)
    content = response.get("content", "")
    if not isinstance(content, str) or not content.strip():
        return empty_judgment(f"repair:{config.repair_model}")
    try:
        return extract_json_object(content)
    except ValueError:
        return {
            **empty_judgment(f"repair:{config.repair_model}"),
            "summary": (
                "OpenCode Go judge returned non-JSON output and the JSON repair pass "
                f"with {config.repair_model} also failed."
            ),
            "judge_error": "json_repair_failed",
            "raw_preview": non_json_output[:1000],
        }


def empty_judgment(model: str) -> dict[str, Any]:
    return {
        "ground_truth_claims": [],
        "agent_claims": [],
        "response_claim_judgments": [],
        "ground_truth_recall_judgments": [],
        "precision": 0.0,
        "recall": 0.0,
        "f1": 0.0,
        "summary": f"OpenCode Go judge model {model} returned empty content; score set to 0.0 for pipeline continuity.",
        "judge_error": "empty_content",
    }


def evaluate_log(base_dir: Path, target: EvalTarget, config: OpenCodeGoJudgeConfig) -> dict[str, Any]:
    path = log_path(base_dir, target)
    if not path.exists():
        raise FileNotFoundError(f"Log file not found: {path}")

    agent_conclusion = extract_single_final_thought(path)
    if not agent_conclusion:
        raise ValueError(f"Could not extract final conclusion from: {path}")

    prompt = add_opencode_go_formatting_addendum(build_judge_prompt(target.task, agent_conclusion))
    judgment = run_opencode_go_judge(prompt, config)
    return {
        "agent": target.agent,
        "model": target.model,
        "task": target.task,
        "timestamp": target.timestamp,
        "judge_provider": "opencode_go",
        "judge_model": config.model,
        "repair_model": config.repair_model,
        "log_path": str(path),
        "agent_conclusion": agent_conclusion,
        "judgment": judgment,
    }


def default_output_path(target: EvalTarget, config: OpenCodeGoJudgeConfig) -> Path:
    return Path("results") / target.model / config.model / f"{target.task}.json"


def write_result_once(output_path: Path, result: dict[str, Any], *, overwrite: bool) -> None:
    if output_path.exists() and not overwrite:
        raise FileExistsError(
            f"Refusing to overwrite existing result: {output_path}. Pass --overwrite to replace it intentionally."
        )
    write_result(output_path, result)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate one FIRE-Bench log with OpenCode Go.")
    parser.add_argument("--agent", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--task", required=True)
    parser.add_argument("--timestamp", required=True)
    parser.add_argument("--base-dir", default="log")
    parser.add_argument("--judge-model", default="qwen3.6-plus")
    parser.add_argument("--repair-model", default="")
    parser.add_argument("--output", default="")
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    target = EvalTarget.from_args(args)
    config = OpenCodeGoJudgeConfig.from_args(args)
    result = evaluate_log(Path(args.base_dir), target, config)

    output_path = Path(args.output) if args.output else default_output_path(target, config)
    write_result_once(output_path, result, overwrite=args.overwrite)

    judgment = result["judgment"]
    print(
        textwrap.dedent(
            f"""\
            OpenCode Go evaluation complete.
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
