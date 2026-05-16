from __future__ import annotations

import argparse
import json
import subprocess
import sys
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Self

RAGCHECKER_DIR = Path(__file__).parent / "RAGChecker"
sys.path.append(str(RAGCHECKER_DIR))

from utils import extract_single_final_thought, gt, query  # noqa: E402

CLAUDE_PROMPT_TEMPLATE = """\
You are a strict claim-level evaluator for a FIRE-Bench result.
Evaluate quantitatively without using external knowledge.

Definitions:
- Split ground truth and agent conclusion into atomic claims.
- A response claim is a true positive only if it is supported by or semantically consistent with at least one ground-truth claim.
- A response claim that contradicts or is not inferable from ground truth is a false positive.
- A ground-truth claim is recovered only if the agent conclusion explicitly states the same idea.
- Precision = true_positive_response_claims / total_response_claims.
- Recall = recovered_ground_truth_claims / total_ground_truth_claims.
- F1 = 2PR/(P+R), or 0 if P+R=0.

Return only JSON with this exact schema:
{{
  "ground_truth_claims": ["..."],
  "agent_claims": ["..."],
  "response_claim_judgments": [
    {{
      "claim": "...",
      "judgment": "TP",
      "matched_ground_truth_indices": [0],
      "reason": "..."
    }}
  ],
  "ground_truth_recall_judgments": [
    {{
      "claim": "...",
      "recovered": true,
      "matched_agent_indices": [0],
      "reason": "..."
    }}
  ],
  "precision": 0.0,
  "recall": 0.0,
  "f1": 0.0,
  "summary": "..."
}}

Task:
{task_query}

Ground truth:
{ground_truth}

Agent conclusion:
{agent_conclusion}
"""


@dataclass(frozen=True, slots=True)
class EvalTarget:
    agent: str
    model: str
    task: str
    timestamp: str

    @classmethod
    def from_args(cls, args: argparse.Namespace) -> Self:
        return cls(agent=args.agent, model=args.model, task=args.task, timestamp=args.timestamp)


@dataclass(frozen=True, slots=True)
class ClaudeJudgeConfig:
    model: str
    claude_bin: str

    @classmethod
    def from_args(cls, args: argparse.Namespace) -> Self:
        return cls(model=args.judge_model, claude_bin=args.claude_bin)


def log_path(base_dir: Path, target: EvalTarget) -> Path:
    return base_dir / target.agent / target.model / target.task / target.timestamp / "log.log"


def build_judge_prompt(task: str, agent_conclusion: str) -> str:
    if task not in query:
        raise ValueError(f"Unknown task query: {task}")
    if task not in gt:
        raise ValueError(f"Unknown task ground truth: {task}")

    return CLAUDE_PROMPT_TEMPLATE.format(
        task_query=query[task],
        ground_truth=gt[task],
        agent_conclusion=agent_conclusion,
    )


def extract_json_object(output: str) -> dict[str, Any]:
    stripped = output.strip()
    if stripped.startswith("```"):
        stripped = stripped.removeprefix("```json").removeprefix("```").strip()
        stripped = stripped.removesuffix("```").strip()

    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError as error:
        raise ValueError(f"Claude judge did not return valid JSON: {output}") from error

    if not isinstance(parsed, dict):
        raise ValueError("Claude judge JSON must be an object")
    return parsed


def run_claude_judge(prompt: str, config: ClaudeJudgeConfig) -> dict[str, Any]:
    process = subprocess.run(
        [config.claude_bin, "-p", prompt, "--model", config.model, "--output-format", "text"],
        check=True,
        capture_output=True,
        text=True,
    )
    return extract_json_object(process.stdout)


def write_result(output_path: Path, result: dict[str, Any]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def evaluate_log(base_dir: Path, target: EvalTarget, config: ClaudeJudgeConfig) -> dict[str, Any]:
    path = log_path(base_dir, target)
    if not path.exists():
        raise FileNotFoundError(f"Log file not found: {path}")

    agent_conclusion = extract_single_final_thought(path)
    if not agent_conclusion:
        raise ValueError(f"Could not extract final conclusion from: {path}")

    prompt = build_judge_prompt(target.task, agent_conclusion)
    judgment = run_claude_judge(prompt, config)
    return {
        "agent": target.agent,
        "model": target.model,
        "task": target.task,
        "timestamp": target.timestamp,
        "judge_model": config.model,
        "log_path": str(path),
        "agent_conclusion": agent_conclusion,
        "judgment": judgment,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate one FIRE-Bench log with Claude Code subscription instead of OpenAI API."
    )
    parser.add_argument("--agent", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--task", required=True)
    parser.add_argument("--timestamp", required=True)
    parser.add_argument("--base-dir", default="log")
    parser.add_argument("--judge-model", default="sonnet")
    parser.add_argument("--claude-bin", default="claude")
    parser.add_argument("--output", default="")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    target = EvalTarget.from_args(args)
    config = ClaudeJudgeConfig.from_args(args)
    result = evaluate_log(Path(args.base_dir), target, config)

    default_output = (
        Path("results")
        / f"claude_subscription_eval_{target.agent}_{target.model}_{target.task}_{target.timestamp}.json"
    )
    output_path = Path(args.output) if args.output else default_output
    write_result(output_path, result)

    judgment = result["judgment"]
    print(
        textwrap.dedent(
            f"""\
            Claude subscription evaluation complete.
            Output: {output_path}
            Precision: {judgment.get("precision")}
            Recall: {judgment.get("recall")}
            F1: {judgment.get("f1")}
            Summary: {judgment.get("summary")}
            """
        ).strip()
    )


if __name__ == "__main__":
    main()
