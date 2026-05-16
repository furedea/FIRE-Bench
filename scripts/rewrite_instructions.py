from __future__ import annotations

import argparse
import difflib
import json
import shutil
from pathlib import Path
from typing import Any


def load_portfolio(path: Path) -> dict[str, dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))


def model_block_for_task(portfolio: dict[str, dict[str, Any]], task: str) -> str:
    if task not in portfolio:
        raise ValueError(f"Unknown task in portfolio: {task}")

    entry = portfolio[task]
    models = entry["models"]
    budget = entry["budget"]
    lines = ["Models:"]
    lines.extend(f"- OpenCode Go: {model}" for model in models)
    lines.extend(
        [
            "- You can call these models using: from utils.llm_inference import LLMInference",
            '- Initialize each model with: LLMInference(provider="opencode_go", model_name=MODEL_NAME)',
            "- Provider: opencode_go",
            "- API key is provided by OPENCODE_API_KEY",
            f"- Computational budget: {budget} API calls per model",
        ]
    )
    return "\n".join(lines)


def rewrite_instruction_text(original: str, block: str) -> str:
    lines = original.splitlines()
    start = next((index for index, line in enumerate(lines) if line.strip() in {"Model:", "Models:"}), None)
    if start is None:
        raise ValueError("Instruction does not contain a Model: or Models: block")

    end = start + 1
    while end < len(lines) and lines[end].strip() != "Datasets:":
        end += 1
    if end == len(lines):
        raise ValueError("Instruction model block is not followed by Datasets:")

    return "\n".join([*lines[:start], block, "", *lines[end:]]) + "\n"


def instruction_path(root: Path, task: str) -> Path:
    return root / "benchmark" / "papers" / task / "instruction" / "instruction.txt"


def backup_path(path: Path) -> Path:
    return path.with_name(f"{path.name}.orig.bak")


def rewrite_instruction(path: Path, block: str, dry_run: bool) -> str:
    backup = backup_path(path)
    source = backup if backup.exists() else path
    original = source.read_text(encoding="utf-8")
    rewritten = rewrite_instruction_text(original, block)
    diff = "".join(
        difflib.unified_diff(
            original.splitlines(keepends=True),
            rewritten.splitlines(keepends=True),
            fromfile=str(source),
            tofile=str(path),
        )
    )

    if dry_run:
        return diff

    if not backup.exists():
        shutil.copy2(path, backup)
    path.write_text(rewritten, encoding="utf-8")
    path.with_name("instruction.diff").write_text(diff, encoding="utf-8")
    return diff


def restore_instruction(path: Path) -> None:
    backup = backup_path(path)
    if not backup.exists():
        raise FileNotFoundError(f"Backup not found: {backup}")
    shutil.copy2(backup, path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Rewrite FIRE-Bench instruction model blocks from a portfolio.")
    parser.add_argument("--portfolio", default="configs/opencode_go_subset.json")
    parser.add_argument("--root", default=".")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--restore", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = Path(args.root)
    portfolio = load_portfolio(root / args.portfolio)

    if not args.dry_run and not args.apply and not args.restore:
        raise SystemExit("Pass one of --dry-run, --apply, or --restore")

    for task in portfolio:
        path = instruction_path(root, task)
        if args.restore:
            restore_instruction(path)
            continue
        diff = rewrite_instruction(path, model_block_for_task(portfolio, task), dry_run=args.dry_run)
        if args.dry_run:
            print(diff)


if __name__ == "__main__":
    main()
