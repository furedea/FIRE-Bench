from __future__ import annotations

import argparse
import ast
import json
import re
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Self

DEFAULT_ARTIFACT_ROOT = Path("repair_agent_artifact")
LEGACY_DEFECTS4J_PROJECTS = {"Chart", "Lang", "Math", "Mockito", "Time"}
BUG_ID_PATTERN = re.compile(r"^([A-Za-z][A-Za-z0-9]*)[-_\s]+(\d+)")
REVIEW_ENTRY_PATTERN = re.compile(r"(?m)^#+\s+([A-Za-z][A-Za-z0-9]*)\s+(\d+)\b")


@dataclass(frozen=True, slots=True)
class BugId:
    project: str
    bug_id: str

    @classmethod
    def parse(cls, text: str) -> Self | None:
        normalized = text.strip().replace(".java", "")
        match = BUG_ID_PATTERN.match(normalized)
        if not match:
            return None
        return cls(project=match.group(1), bug_id=match.group(2))

    @property
    def key(self) -> str:
        return f"{self.project}-{self.bug_id}"

    @property
    def is_legacy_defects4j_project(self) -> bool:
        if self.project in LEGACY_DEFECTS4J_PROJECTS:
            return True
        return self.project == "Closure" and int(self.bug_id) <= 133


def build_summary(artifact_root: Path = DEFAULT_ARTIFACT_ROOT) -> dict[str, Any]:
    artifact_root = artifact_root.resolve()
    setup_root = artifact_root / "repair_agent" / "experimental_setups"
    main_table = load_main_table_inputs(setup_root / "generate_main_table.py")
    correct_bugs = parse_bug_lines(read_lines(artifact_root / "data" / "final_list_of_fixed_bugs"))
    repair_agent_bugs = tuple(main_table["repair_agent_list"])
    baseline_bugs = {
        "ChatRepair": tuple(main_table["chatgpt_fixes"]),
        "ITER": tuple(main_table["iterlist"]),
        "SelfAPR": tuple(main_table["self_apr"]),
    }
    baseline_union = set().union(*(set(bugs) for bugs in baseline_bugs.values()))
    exclusive_bugs = tuple(sorted(set(correct_bugs) - baseline_union))

    return {
        "artifact_root": str(artifact_root),
        "defects4j": {
            "total_bugs": sum(main_table["total_bugs"].values()),
            "bugs_by_project": main_table["total_bugs"],
        },
        "repair_agent": {
            "correct_total": len(set(correct_bugs)),
            "correct_by_project": count_by_project(correct_bugs),
            "correct_list_matches_generate_main_table": set(correct_bugs) == set(repair_agent_bugs),
            "plausible_manual_analysis_total": sum(main_table["plausibles"].values()),
            "plausible_manual_analysis_by_project": main_table["plausibles"],
            "version_split": version_split(correct_bugs),
            "exclusive_vs_compared_baselines": {
                "count": len(exclusive_bugs),
                "bugs": exclusive_bugs,
            },
        },
        "baselines": {name: baseline_summary(bugs, correct_bugs) for name, bugs in baseline_bugs.items()},
        "manual_review_labels": review_label_summary(artifact_root / "data" / "fixes_implementation"),
        "gitbug_java": gitbug_sample_summary(setup_root / "gitbuglist"),
        "limitations": [
            "The artifact exposes the GitBug-Java sample list but not full GitBug execution results.",
            "The artifact does not expose enough ablation logs to reconstruct ablation counts directly.",
            "The manual review file is useful for provenance, but not every correct fix has a structured label.",
        ],
    }


def load_main_table_inputs(path: Path) -> dict[str, Any]:
    source = path.read_text(encoding="utf-8")
    return {
        "self_apr": parse_bug_lines(evaluate_assignment(source, "self_apr").splitlines()),
        "chatgpt_fixes": parse_bug_lines(evaluate_assignment(source, "chatgpt_fixes").splitlines()),
        "iterlist": parse_bug_lines(evaluate_assignment(source, "iterlist").splitlines()),
        "repair_agent_list": parse_bug_lines(evaluate_assignment(source, "repair_agent_list").splitlines()),
        "total_bugs": evaluate_assignment(source, "total_bugs"),
        "plausibles": evaluate_assignment(source, "plausibles"),
    }


def evaluate_assignment(source: str, name: str) -> Any:
    tree = ast.parse(source)
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if any(isinstance(target, ast.Name) and target.id == name for target in node.targets):
            return evaluate_literal_expression(node.value)
    raise KeyError(f"Assignment not found: {name}")


def evaluate_literal_expression(node: ast.AST) -> Any:
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Dict):
        return ast.literal_eval(node)
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "replace":
        value = evaluate_literal_expression(node.func.value)
        old, new = (evaluate_literal_expression(argument) for argument in node.args)
        return value.replace(old, new)
    raise ValueError(f"Unsupported expression in aggregate input: {ast.dump(node)}")


def read_lines(path: Path) -> tuple[str, ...]:
    return tuple(path.read_text(encoding="utf-8").splitlines())


def parse_bug_lines(lines: Iterable[str]) -> tuple[str, ...]:
    bugs = []
    for line in lines:
        bug = BugId.parse(line)
        if bug:
            bugs.append(bug.key)
    return tuple(bugs)


def count_by_project(bugs: Iterable[str]) -> dict[str, int]:
    counts = Counter(bug.split("-", maxsplit=1)[0] for bug in bugs)
    return dict(sorted(counts.items()))


def version_split(bugs: Iterable[str]) -> dict[str, int]:
    counts = Counter()
    for text in bugs:
        bug = BugId.parse(text)
        if not bug:
            continue
        key = "legacy_defects4j_projects" if bug.is_legacy_defects4j_project else "additional_defects4j_2_projects"
        counts[key] += 1
    return {
        "legacy_defects4j_projects": counts["legacy_defects4j_projects"],
        "additional_defects4j_2_projects": counts["additional_defects4j_2_projects"],
    }


def baseline_summary(bugs: tuple[str, ...], repair_agent_bugs: tuple[str, ...]) -> dict[str, Any]:
    unique_bugs = set(bugs)
    repair_agent_set = set(repair_agent_bugs)
    return {
        "raw_total": len(bugs),
        "unique_total": len(unique_bugs),
        "overlap_with_repair_agent": len(unique_bugs & repair_agent_set),
        "version_split": version_split(unique_bugs),
    }


def review_label_summary(path: Path) -> dict[str, Any]:
    source = path.read_text(encoding="utf-8")
    counts = Counter()
    for block in review_entry_blocks(source):
        label = review_label(block)
        if label:
            counts[label] += 1
    return {
        "counts": dict(sorted(counts.items())),
        "reviewed_entry_count": sum(counts.values()),
    }


def review_entry_blocks(source: str) -> tuple[str, ...]:
    matches = tuple(REVIEW_ENTRY_PATTERN.finditer(source))
    blocks = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(source)
        blocks.append(source[match.start() : end])
    return tuple(blocks)


def review_label(block: str) -> str:
    match = re.search(r"(?im)^#+\s*why:\s*\n\s*([^\n]+)", block)
    if not match:
        return ""
    label = match.group(1).strip().rstrip(".").lower()
    if "good enough" in label:
        return "good_enough"
    if "semantic" in label:
        return "semantically_equivalent"
    if "identical" in label:
        return "identical"
    return label.replace(" ", "_")


def gitbug_sample_summary(path: Path) -> dict[str, int]:
    bugs = tuple(line.strip() for line in read_lines(path) if line.strip())
    return {
        "sample_total": len(bugs),
        "unique_sample_total": len(set(bugs)),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Reconstruct RepairAgent aggregate counts from released artifact inputs."
    )
    parser.add_argument("--artifact-root", default=DEFAULT_ARTIFACT_ROOT, type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    print(json.dumps(build_summary(args.artifact_root), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
