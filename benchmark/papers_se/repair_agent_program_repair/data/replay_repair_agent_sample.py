from __future__ import annotations

import argparse
import ast
import json
import os
import re
import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DEFAULT_ARTIFACT_ROOT = Path("repair_agent_artifact")
DEFAULT_BUGS_FILE = Path("bug_sample.txt")
DEFAULT_OUTPUT = Path("tmp_results") / "repair_agent_sample_replay.jsonl"
DEFAULT_WORK_ROOT = Path("tmp_defects4j_replay")
FAILING_TESTS_PATTERN = re.compile(r"Failing tests:\s*(\d+)")


@dataclass(frozen=True, slots=True)
class Defects4JBug:
    project: str
    bug_id: int

    @property
    def key(self) -> str:
        return f"{self.project}-{self.bug_id}"


@dataclass(frozen=True, slots=True)
class PatchCandidate:
    bug: Defects4JBug
    source_path: Path
    source_index: int
    candidate_order: int
    changes: tuple[dict[str, Any], ...]

    @property
    def key(self) -> str:
        return f"{self.bug.key}:{self.source_path.as_posix()}:{self.source_index}"


@dataclass(frozen=True, slots=True)
class Defects4JTestResult:
    return_code: int
    output: str
    failing_tests: int | None

    @property
    def plausible(self) -> bool:
        return self.failing_tests == 0


@dataclass(frozen=True, slots=True)
class ReplayRecord:
    bug: str
    candidate_order: int
    candidate_key: str
    applied: bool
    plausible: bool
    failing_tests: int | None
    return_code: int | None
    seconds: float
    error: str

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "bug": self.bug,
            "candidate_order": self.candidate_order,
            "candidate_key": self.candidate_key,
            "applied": self.applied,
            "plausible": self.plausible,
            "failing_tests": self.failing_tests,
            "return_code": self.return_code,
            "seconds": self.seconds,
            "error": self.error,
        }


def read_bug_sample(path: Path) -> tuple[Defects4JBug, ...]:
    bugs: list[Defects4JBug] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        project, bug_id = stripped.split()
        bugs.append(Defects4JBug(project=project, bug_id=int(bug_id)))
    return tuple(bugs)


def select_bugs(bugs: tuple[Defects4JBug, ...], selected_keys: tuple[str, ...]) -> tuple[Defects4JBug, ...]:
    if not selected_keys:
        return bugs
    selected = set(selected_keys)
    return tuple(bug for bug in bugs if bug.key in selected)


def collect_candidates(
    *,
    artifact_root: Path,
    bugs: tuple[Defects4JBug, ...],
    max_candidates_per_bug: int,
) -> tuple[PatchCandidate, ...]:
    patch_dir = artifact_root / "data" / "derivated_patches"
    candidates: list[PatchCandidate] = []
    for bug in bugs:
        bug_candidates = patch_candidates_for_bug(patch_dir, bug)
        candidates.extend(bug_candidates[:max_candidates_per_bug])
    return tuple(candidates)


def patch_candidates_for_bug(patch_dir: Path, bug: Defects4JBug) -> tuple[PatchCandidate, ...]:
    pattern = f"experiment_*mutants_{bug.project}_{bug.bug_id}.json"
    candidates: list[PatchCandidate] = []
    for path in sorted(patch_dir.glob(pattern)):
        if "_raw_" in path.name:
            continue
        for source_index, changes in enumerate(load_candidate_changes_or_empty(path)):
            candidates.append(
                PatchCandidate(
                    bug=bug,
                    source_path=path,
                    source_index=source_index,
                    candidate_order=len(candidates),
                    changes=changes,
                )
            )
    return tuple(candidates)


def load_candidate_changes_or_empty(path: Path) -> tuple[tuple[dict[str, Any], ...], ...]:
    try:
        return load_candidate_changes(path)
    except (SyntaxError, ValueError, json.JSONDecodeError):
        return ()


def load_candidate_changes(path: Path) -> tuple[tuple[dict[str, Any], ...], ...]:
    text = path.read_text(encoding="utf-8")
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        data = load_prompt_response_candidate_data(text, path)
    if not isinstance(data, list):
        raise ValueError(f"Expected a JSON list in {path}")
    return tuple(normalize_candidate(candidate) for candidate in data)


def load_prompt_response_candidate_data(text: str, path: Path) -> Any:
    wrapper = ast.literal_eval(text)
    if not isinstance(wrapper, dict) or not isinstance(wrapper.get("response"), str):
        raise ValueError(f"Expected JSON list or prompt/response wrapper in {path}")
    return json.loads(wrapper["response"])


def normalize_candidate(candidate: Any) -> tuple[dict[str, Any], ...]:
    if isinstance(candidate, dict):
        return (candidate,)
    if isinstance(candidate, list) and all(isinstance(item, dict) for item in candidate):
        return tuple(candidate)
    raise ValueError(f"Unsupported patch candidate shape: {candidate!r}")


def parse_defects4j_test_result(return_code: int, stdout: str, stderr: str) -> Defects4JTestResult:
    output = stdout + stderr
    match = FAILING_TESTS_PATTERN.search(output)
    failing_tests = int(match.group(1)) if match else None
    return Defects4JTestResult(
        return_code=return_code,
        output=output,
        failing_tests=failing_tests,
    )


def replay_candidates(
    *,
    candidates: tuple[PatchCandidate, ...],
    work_root: Path,
    output: Path,
    timeout_seconds: int,
    keep_workdirs: bool,
) -> tuple[ReplayRecord, ...]:
    if work_root.exists() and not keep_workdirs:
        shutil.rmtree(work_root)
    work_root.mkdir(parents=True, exist_ok=True)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("", encoding="utf-8")

    env = defects4j_environment(work_root)
    records: list[ReplayRecord] = []
    for candidate in candidates:
        record = replay_candidate(
            candidate=candidate,
            work_root=work_root,
            env=env,
            timeout_seconds=timeout_seconds,
            keep_workdirs=keep_workdirs,
        )
        records.append(record)
        append_jsonl(output, record.to_jsonable())
    return tuple(records)


def replay_candidate(
    *,
    candidate: PatchCandidate,
    work_root: Path,
    env: dict[str, str],
    timeout_seconds: int,
    keep_workdirs: bool,
) -> ReplayRecord:
    start = time.monotonic()
    candidate_root = work_root / f"{candidate.bug.key}-candidate-{candidate.candidate_order}"
    if candidate_root.exists():
        shutil.rmtree(candidate_root)

    try:
        checkout_bug(candidate.bug, candidate_root, env, timeout_seconds)
        apply_candidate(candidate_root, candidate)
        test_result = run_defects4j_test(candidate_root, env, timeout_seconds)
        error = "" if test_result.failing_tests is not None else "Defects4J output did not report failing tests"
        return ReplayRecord(
            bug=candidate.bug.key,
            candidate_order=candidate.candidate_order,
            candidate_key=candidate.key,
            applied=True,
            plausible=test_result.plausible,
            failing_tests=test_result.failing_tests,
            return_code=test_result.return_code,
            seconds=round(time.monotonic() - start, 2),
            error=error,
        )
    except Exception as error:
        return ReplayRecord(
            bug=candidate.bug.key,
            candidate_order=candidate.candidate_order,
            candidate_key=candidate.key,
            applied=False,
            plausible=False,
            failing_tests=None,
            return_code=None,
            seconds=round(time.monotonic() - start, 2),
            error=str(error),
        )
    finally:
        if candidate_root.exists() and not keep_workdirs:
            shutil.rmtree(candidate_root)


def defects4j_environment(work_root: Path) -> dict[str, str]:
    git_config = work_root / "gitconfig"
    git_config.write_text(sandbox_git_config_content(), encoding="utf-8")
    env = os.environ.copy()
    env.update(
        {
            "GIT_CONFIG_GLOBAL": str(git_config),
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_AUTHOR_NAME": "FIRE-Bench",
            "GIT_AUTHOR_EMAIL": "fire-bench@example.invalid",
            "GIT_COMMITTER_NAME": "FIRE-Bench",
            "GIT_COMMITTER_EMAIL": "fire-bench@example.invalid",
        }
    )
    return env


def sandbox_git_config_content() -> str:
    return "\n".join(
        [
            "[user]",
            "\tname = FIRE-Bench",
            "\temail = fire-bench@example.invalid",
            "[commit]",
            "\tgpgsign = false",
            "[tag]",
            "\tgpgsign = false",
            "",
        ]
    )


def checkout_bug(
    bug: Defects4JBug,
    destination: Path,
    env: dict[str, str],
    timeout_seconds: int,
) -> None:
    run_command(
        [
            "defects4j",
            "checkout",
            "-p",
            bug.project,
            "-v",
            f"{bug.bug_id}b",
            "-w",
            str(destination),
        ],
        env=env,
        timeout_seconds=timeout_seconds,
    )


def run_defects4j_test(
    work_dir: Path,
    env: dict[str, str],
    timeout_seconds: int,
) -> Defects4JTestResult:
    completed = run_command(
        ["defects4j", "test"],
        cwd=work_dir,
        env=env,
        timeout_seconds=timeout_seconds,
        check=False,
    )
    return parse_defects4j_test_result(
        return_code=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )


def run_command(
    command: list[str],
    *,
    env: dict[str, str],
    timeout_seconds: int,
    cwd: Path | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        timeout=timeout_seconds,
        check=False,
    )
    if check and completed.returncode != 0:
        output = completed.stdout + completed.stderr
        raise RuntimeError(f"Command failed: {' '.join(command)}\n{output[-4000:]}")
    return completed


def apply_candidate(work_dir: Path, candidate: PatchCandidate) -> None:
    for change in candidate.changes:
        target = find_target_file(work_dir, str(change["file_name"]))
        lines = target.read_text(encoding="utf-8").splitlines()
        apply_change_lines(lines, change)
        target.write_text("\n".join(lines) + "\n", encoding="utf-8")


def find_target_file(work_dir: Path, file_name: str) -> Path:
    direct_path = work_dir / file_name
    if direct_path.exists():
        return direct_path

    normalized_name = Path(file_name).as_posix()
    matches = [
        path
        for path in work_dir.rglob(Path(file_name).name)
        if path.is_file() and path.relative_to(work_dir).as_posix().endswith(normalized_name)
    ]
    if len(matches) != 1:
        raise FileNotFoundError(f"Expected one match for {file_name}, found {len(matches)}")
    return matches[0]


def apply_change_lines(lines: list[str], change: dict[str, Any]) -> None:
    for deletion in sorted(change.get("deletions", []), key=line_number, reverse=True):
        delete_line(lines, line_number(deletion))
    for modification in sorted(change.get("modifications", []), key=line_number, reverse=True):
        modify_line(lines, line_number(modification), str(modification["modified_line"]))
    for insertion in sorted(change.get("insertions", []), key=line_number, reverse=True):
        insert_lines(lines, line_number(insertion), tuple(str(line) for line in insertion["new_lines"]))


def line_number(operation: Any) -> int:
    if isinstance(operation, int):
        return operation
    if isinstance(operation, dict):
        return int(operation["line_number"])
    raise ValueError(f"Unsupported line operation: {operation!r}")


def delete_line(lines: list[str], number: int) -> None:
    assert_line_number(lines, number)
    del lines[number - 1]


def modify_line(lines: list[str], number: int, replacement: str) -> None:
    assert_line_number(lines, number)
    lines[number - 1] = replacement


def insert_lines(lines: list[str], number: int, new_lines: tuple[str, ...]) -> None:
    if number < 1 or number > len(lines) + 1:
        raise IndexError(f"Line number {number} is outside 1..{len(lines) + 1}")
    lines[number - 1 : number - 1] = list(new_lines)


def assert_line_number(lines: list[str], number: int) -> None:
    if number < 1 or number > len(lines):
        raise IndexError(f"Line number {number} is outside 1..{len(lines)}")


def append_jsonl(path: Path, data: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(data, sort_keys=True) + "\n")


def summarize(records: tuple[ReplayRecord, ...]) -> dict[str, Any]:
    return {
        "candidates": len(records),
        "applied": sum(record.applied for record in records),
        "plausible": sum(record.plausible for record in records),
        "bugs": sorted({record.bug for record in records}),
        "plausible_bugs": sorted({record.bug for record in records if record.plausible}),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Replay bounded RepairAgent patch candidates on Defects4J.")
    parser.add_argument("--artifact-root", type=Path, default=DEFAULT_ARTIFACT_ROOT)
    parser.add_argument("--bugs-file", type=Path, default=DEFAULT_BUGS_FILE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--work-root", type=Path, default=DEFAULT_WORK_ROOT)
    parser.add_argument("--max-candidates-per-bug", type=int, default=1)
    parser.add_argument("--timeout-seconds", type=int, default=900)
    parser.add_argument("--bug", action="append", default=[])
    parser.add_argument("--keep-workdirs", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    bugs = select_bugs(read_bug_sample(args.bugs_file), tuple(args.bug))
    candidates = collect_candidates(
        artifact_root=args.artifact_root,
        bugs=bugs,
        max_candidates_per_bug=args.max_candidates_per_bug,
    )
    records = replay_candidates(
        candidates=candidates,
        work_root=args.work_root,
        output=args.output,
        timeout_seconds=args.timeout_seconds,
        keep_workdirs=args.keep_workdirs,
    )
    print(json.dumps(summarize(records), indent=2, sort_keys=True))
    print(f"Wrote JSONL results to {args.output}")


if __name__ == "__main__":
    main()
