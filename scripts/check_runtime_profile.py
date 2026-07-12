from __future__ import annotations

import argparse
import json
import os
import shutil
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROFILE_DIR = REPO_ROOT / "runtime-profiles"


@dataclass(frozen=True, slots=True)
class RuntimeProfile:
    profile_id: str
    required_commands: tuple[str, ...]
    required_environment: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RuntimePreflightResult:
    ok: bool
    profile_id: str
    missing_commands: tuple[str, ...]
    missing_environment: tuple[str, ...]

    def message(self) -> str:
        if self.ok:
            return f"Runtime profile '{self.profile_id}' is available."

        parts = [f"Infrastructure failure: runtime profile '{self.profile_id}' is not available."]
        if self.missing_commands:
            parts.append(f"Missing commands: {', '.join(self.missing_commands)}.")
        if self.missing_environment:
            parts.append(f"Missing environment variables: {', '.join(self.missing_environment)}.")
        return " ".join(parts)


def runtime_profile_for_task(task_root: Path) -> str | None:
    task_config = task_root / "task_config.yaml"
    if not task_config.exists():
        return None

    for line in task_config.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("runtime_profile:"):
            value = stripped.split(":", 1)[1].strip()
            return value.strip("\"'") or None
    return None


def load_runtime_profile(
    profile_id: str,
    profile_dir: Path = DEFAULT_PROFILE_DIR,
) -> RuntimeProfile:
    profile_path = profile_dir / f"{profile_id.replace('-', '_')}.json"
    data = json.loads(profile_path.read_text(encoding="utf-8"))
    return RuntimeProfile(
        profile_id=data["id"],
        required_commands=tuple(data.get("required_commands", [])),
        required_environment=tuple(data.get("required_environment", [])),
    )


def check_runtime_profile(
    profile_id: str,
    profile_dir: Path = DEFAULT_PROFILE_DIR,
    which: Callable[[str], str | None] = shutil.which,
    environ: Mapping[str, str] = os.environ,
) -> RuntimePreflightResult:
    profile = load_runtime_profile(profile_id, profile_dir)
    missing_commands = tuple(command for command in profile.required_commands if which(command) is None)
    missing_environment = tuple(name for name in profile.required_environment if not environ.get(name))
    return RuntimePreflightResult(
        ok=not missing_commands and not missing_environment,
        profile_id=profile.profile_id,
        missing_commands=missing_commands,
        missing_environment=missing_environment,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Check a FIRE-Bench runtime profile.")
    parser.add_argument("--profile", help="Runtime profile id to check.")
    parser.add_argument("--task-root", type=Path, help="Task root containing task_config.yaml.")
    args = parser.parse_args()

    profile_id = args.profile
    if not profile_id and args.task_root:
        profile_id = runtime_profile_for_task(args.task_root)
    if not profile_id:
        raise SystemExit("No runtime profile was provided or declared by the task.")

    result = check_runtime_profile(profile_id)
    print(result.message())
    raise SystemExit(0 if result.ok else 125)


if __name__ == "__main__":
    main()
