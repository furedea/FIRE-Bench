from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


llm_module = load_module("firebench_llm_inference", ROOT_DIR / "utils" / "llm_inference.py")
eval_module = load_module("firebench_opencode_go_eval", ROOT_DIR / "eval" / "opencode_go_eval.py")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Diagnose OpenCode Go judge responses without changing prompts.")
    parser.add_argument("--agent", required=True)
    parser.add_argument("--outer-model", required=True)
    parser.add_argument("--task", required=True)
    parser.add_argument("--timestamp", required=True)
    parser.add_argument("--base-dir", default="log")
    parser.add_argument("--models", nargs="+", default=["deepseek-v4-flash", "deepseek-v4-pro", "qwen3.6-plus"])
    parser.add_argument("--out", default="")
    return parser.parse_args()


def call_model(model: str, prompt: str) -> dict[str, Any]:
    inference = llm_module.LLMInference(provider="opencode_go", model_name=model)
    try:
        response = inference.generate(prompt, max_tokens=512, temperature=0)
    except Exception as error:
        return {"model": model, "ok": False, "error": repr(error)}

    content = response.get("content", "")
    return {
        "model": model,
        "ok": True,
        "content_length": len(content) if isinstance(content, str) else None,
        "content_preview": content[:500] if isinstance(content, str) else repr(content),
        "usage": {
            "input_tokens": response.get("input_tokens"),
            "output_tokens": response.get("output_tokens"),
            "total_tokens": response.get("total_tokens"),
        },
    }


def main() -> None:
    args = parse_args()
    if not os.getenv("OPENCODE_API_KEY"):
        raise SystemExit("OPENCODE_API_KEY is required")

    target = eval_module.EvalTarget(
        agent=args.agent,
        model=args.outer_model,
        task=args.task,
        timestamp=args.timestamp,
    )
    log_path = eval_module.log_path(Path(args.base_dir), target)
    conclusion = eval_module.extract_single_final_thought(log_path)
    if not conclusion:
        raise SystemExit(f"Could not extract final conclusion from {log_path}")

    judge_prompt = eval_module.build_judge_prompt(args.task, conclusion)
    smoke_prompt = 'Return exactly this JSON and nothing else: {"ok": true}'
    compact_prompt = (
        "Return valid JSON only. Score this answer roughly with keys precision, recall, f1, summary.\n\n"
        f"Task: {args.task}\n\nAgent conclusion:\n{conclusion[:4000]}"
    )

    report = {
        "task": args.task,
        "timestamp": args.timestamp,
        "log_path": str(log_path),
        "agent_conclusion_chars": len(conclusion),
        "judge_prompt_chars": len(judge_prompt),
        "smoke": [call_model(model, smoke_prompt) for model in args.models],
        "compact": [call_model(model, compact_prompt) for model in args.models],
        "full_judge": [call_model(model, judge_prompt) for model in args.models],
    }

    text = json.dumps(report, indent=2, ensure_ascii=False)
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
