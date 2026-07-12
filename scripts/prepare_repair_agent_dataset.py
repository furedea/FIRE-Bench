from __future__ import annotations

import argparse
import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DEFAULT_OUTPUT_ROOT = Path("benchmark/papers_se/repair_agent_program_repair/data/repair_agent_artifact")
ALLOWED_PREFIXES = (
    "repair_agent/",
    "experimental_setups/",
    "data/root_patches/",
    "data/derivated_patches/",
    "data/derived_patches/",
    "data/patches/",
)
ALLOWED_SUFFIXES = (
    ".cfg",
    ".csv",
    ".diff",
    ".java",
    ".json",
    ".patch",
    ".properties",
    ".py",
    ".sh",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
)
ALLOWED_FILE_NAMES = {"Dockerfile", "LICENSE"}
AGGREGATE_INPUT_PATHS = {
    "data/final_list_of_fixed_bugs",
    "data/fixes_implementation",
    "repair_agent/experimental_setups/analyze_experiment_results.py",
    "repair_agent/experimental_setups/bugs_list",
    "repair_agent/experimental_setups/chatrepair_all",
    "repair_agent/experimental_setups/draw_venn_chatrepair_clean.py",
    "repair_agent/experimental_setups/generate_main_table.py",
    "repair_agent/experimental_setups/gitbuglist",
}
DENIED_FILE_NAMES = {"README", "README.md", "README.rst"}
DENIED_EXACT_PATHS = {
    "repair_agent/model_logging_temp.txt",
}
DENIED_PREFIXES = ("repair_agent/autogpt/workspace/",)
DENIED_PATH_TOKENS = (
    "final_list",
    "fixed_bugs",
    "fixed_so_far",
    "fixes_implementation",
    "main_table",
    "paper",
    "result",
    "table",
    "venn",
)


@dataclass(frozen=True, slots=True)
class DatasetManifest:
    source_root: Path
    output_root: Path
    copied_paths: tuple[Path, ...]
    skipped_paths: tuple[Path, ...]

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "source_root": self.source_root.name,
            "output_root": ".",
            "copied_paths": [path.as_posix() for path in self.copied_paths],
            "skipped_paths": [path.as_posix() for path in self.skipped_paths],
        }


def prepare_dataset(
    artifact_root: Path, output_root: Path = DEFAULT_OUTPUT_ROOT, *, dry_run: bool = False
) -> DatasetManifest:
    artifact_root = artifact_root.resolve()
    output_root = output_root.resolve()
    relative_paths = artifact_file_paths(artifact_root)
    copied_paths = tuple(path for path in relative_paths if should_copy(path))
    skipped_paths = tuple(path for path in relative_paths if path not in copied_paths)
    manifest = DatasetManifest(
        source_root=artifact_root,
        output_root=output_root,
        copied_paths=copied_paths,
        skipped_paths=skipped_paths,
    )

    if dry_run:
        return manifest

    ensure_empty_output(output_root)
    for relative_path in copied_paths:
        copy_artifact_file(artifact_root, output_root, relative_path)
    write_manifest(output_root, manifest)
    return manifest


def artifact_file_paths(artifact_root: Path) -> tuple[Path, ...]:
    if not artifact_root.exists():
        raise FileNotFoundError(f"Artifact root does not exist: {artifact_root}")
    if not artifact_root.is_dir():
        raise NotADirectoryError(f"Artifact root must be a directory: {artifact_root}")
    return tuple(
        sorted(
            (path.relative_to(artifact_root) for path in artifact_root.rglob("*") if path.is_file()),
            key=lambda path: path.as_posix(),
        )
    )


def should_copy(relative_path: Path) -> bool:
    normalized = relative_path.as_posix()
    lowered = normalized.lower()
    if normalized in DENIED_EXACT_PATHS:
        return False
    if normalized.startswith(DENIED_PREFIXES):
        return False
    if relative_path.name in DENIED_FILE_NAMES:
        return False
    if normalized in AGGREGATE_INPUT_PATHS:
        return True
    if any(token in lowered for token in DENIED_PATH_TOKENS):
        return False
    if normalized.startswith("data/root_patches/"):
        return True
    if relative_path.name in ALLOWED_FILE_NAMES:
        return True
    if relative_path.suffix.lower() not in ALLOWED_SUFFIXES:
        return False
    return any(normalized.startswith(prefix) for prefix in ALLOWED_PREFIXES)


def ensure_empty_output(output_root: Path) -> None:
    if output_root.exists() and any(output_root.iterdir()):
        raise FileExistsError(f"Output directory must be empty or absent: {output_root}")
    output_root.mkdir(parents=True, exist_ok=True)


def copy_artifact_file(artifact_root: Path, output_root: Path, relative_path: Path) -> None:
    destination = output_root / relative_path
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(artifact_root / relative_path, destination)


def write_manifest(output_root: Path, manifest: DatasetManifest) -> None:
    path = output_root / "_manifest.json"
    path.write_text(json.dumps(manifest.to_jsonable(), indent=2) + "\n", encoding="utf-8")


def manifest_summary(manifest: DatasetManifest, limit: int = 20) -> str:
    lines = [
        f"source_root: {manifest.source_root}",
        f"output_root: {manifest.output_root}",
        f"copied_count: {len(manifest.copied_paths)}",
        f"skipped_count: {len(manifest.skipped_paths)}",
        "copied_examples:",
    ]
    lines.extend(f"- {path.as_posix()}" for path in manifest.copied_paths[:limit])
    lines.append("skipped_examples:")
    lines.extend(f"- {path.as_posix()}" for path in manifest.skipped_paths[:limit])
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare a sanitized RepairAgent artifact subset for FIRE-Bench-SE.")
    parser.add_argument("--artifact-root", required=True, type=Path)
    parser.add_argument("--output", default=DEFAULT_OUTPUT_ROOT, type=Path)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--summary", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    manifest = prepare_dataset(args.artifact_root, args.output, dry_run=args.dry_run)
    if args.summary:
        print(manifest_summary(manifest))
        return
    print(json.dumps(manifest.to_jsonable(), indent=2))


if __name__ == "__main__":
    main()
