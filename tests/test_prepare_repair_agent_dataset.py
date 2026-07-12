import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.prepare_repair_agent_dataset import manifest_summary, prepare_dataset


def write_file(path: Path, content: str = "content\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_prepare_dataset_copies_patch_evidence_without_upstream_runtime_code(tmp_path: Path) -> None:
    artifact = tmp_path / "artifact"
    output = tmp_path / "output"
    write_file(artifact / "repair_agent" / "agent.py")
    write_file(artifact / "repair_agent" / "Dockerfile")
    write_file(artifact / "repair_agent" / "experimental_setups" / "d4j12.csv")
    write_file(artifact / "data" / "root_patches" / "Chart" / "1" / "patch.diff")

    manifest = prepare_dataset(artifact, output)

    assert manifest.copied_paths == (Path("data/root_patches/Chart/1/patch.diff"),)
    assert not (output / "repair_agent" / "agent.py").exists()
    assert not (output / "repair_agent" / "Dockerfile").exists()
    assert not (output / "repair_agent" / "experimental_setups" / "d4j12.csv").exists()
    assert (output / "data" / "root_patches" / "Chart" / "1" / "patch.diff").is_file()


def test_prepare_dataset_copies_released_aggregate_reconstruction_inputs(tmp_path: Path) -> None:
    artifact = tmp_path / "artifact"
    output = tmp_path / "output"
    write_file(artifact / "repair_agent" / "agent.py")
    write_file(artifact / "data" / "final_list_of_fixed_bugs")
    write_file(artifact / "data" / "fixes_implementation")
    write_file(artifact / "repair_agent" / "experimental_setups" / "generate_main_table.py")
    write_file(artifact / "repair_agent" / "experimental_setups" / "draw_venn_chatrepair_clean.py")
    write_file(artifact / "repair_agent" / "experimental_setups" / "chatrepair_all")
    write_file(artifact / "repair_agent" / "experimental_setups" / "gitbuglist")
    write_file(artifact / "repair_agent" / "experimental_setups" / "bugs_list")
    write_file(artifact / "repair_agent" / "experimental_setups" / "analyze_experiment_results.py")
    write_file(artifact / "scripts" / "generate_main_table.py")
    write_file(artifact / "paper" / "repair_agent.pdf")

    manifest = prepare_dataset(artifact, output)

    assert manifest.copied_paths == (
        Path("data/final_list_of_fixed_bugs"),
        Path("data/fixes_implementation"),
        Path("repair_agent/experimental_setups/analyze_experiment_results.py"),
        Path("repair_agent/experimental_setups/bugs_list"),
        Path("repair_agent/experimental_setups/chatrepair_all"),
        Path("repair_agent/experimental_setups/draw_venn_chatrepair_clean.py"),
        Path("repair_agent/experimental_setups/generate_main_table.py"),
        Path("repair_agent/experimental_setups/gitbuglist"),
    )
    assert (output / "data" / "final_list_of_fixed_bugs").is_file()
    assert (output / "data" / "fixes_implementation").is_file()
    assert (output / "repair_agent" / "experimental_setups" / "generate_main_table.py").is_file()
    assert (output / "repair_agent" / "experimental_setups" / "draw_venn_chatrepair_clean.py").is_file()
    assert not (output / "scripts" / "generate_main_table.py").exists()
    assert not (output / "paper" / "repair_agent.pdf").exists()


def test_prepare_dataset_copies_extensionless_root_patches_and_derivated_patches(tmp_path: Path) -> None:
    artifact = tmp_path / "artifact"
    output = tmp_path / "output"
    write_file(artifact / "data" / "root_patches" / "413_Chart_6")
    write_file(artifact / "data" / "derivated_patches" / "experiment_413mutants_Chart_6.json")
    write_file(artifact / "repair_agent" / "experimental_setups" / "fixed_so_far")

    manifest = prepare_dataset(artifact, output)

    assert manifest.copied_paths == (
        Path("data/derivated_patches/experiment_413mutants_Chart_6.json"),
        Path("data/root_patches/413_Chart_6"),
    )
    assert (output / "data" / "root_patches" / "413_Chart_6").is_file()
    assert (output / "data" / "derivated_patches" / "experiment_413mutants_Chart_6.json").is_file()
    assert not (output / "repair_agent" / "experimental_setups" / "fixed_so_far").exists()


def test_prepare_dataset_excludes_runtime_workspace_and_model_log(tmp_path: Path) -> None:
    artifact = tmp_path / "artifact"
    output = tmp_path / "output"
    write_file(artifact / "repair_agent" / "agent.py")
    write_file(artifact / "repair_agent" / "model_logging_temp.txt")
    write_file(artifact / "repair_agent" / "autogpt" / "workspace" / "BubbleSort.java")

    manifest = prepare_dataset(artifact, output)

    assert manifest.copied_paths == ()
    assert not (output / "repair_agent" / "model_logging_temp.txt").exists()
    assert not (output / "repair_agent" / "autogpt" / "workspace").exists()


def test_manifest_does_not_store_local_absolute_paths(tmp_path: Path) -> None:
    artifact = tmp_path / "artifact"
    output = tmp_path / "output"
    write_file(artifact / "repair_agent" / "agent.py")

    prepare_dataset(artifact, output)

    manifest = json.loads((output / "_manifest.json").read_text(encoding="utf-8"))
    assert manifest["source_root"] == "artifact"
    assert manifest["output_root"] == "."


def test_prepare_dataset_excludes_upstream_dependency_manifests(tmp_path: Path) -> None:
    artifact = tmp_path / "artifact"
    output = tmp_path / "output"
    write_file(artifact / "repair_agent" / "requirements.txt", "gitpython==3.1.31\n")
    write_file(artifact / "repair_agent" / "pyproject.toml")

    manifest = prepare_dataset(artifact, output)

    assert manifest.copied_paths == ()


def test_manifest_summary_reports_counts_and_examples(tmp_path: Path) -> None:
    artifact = tmp_path / "artifact"
    output = tmp_path / "output"
    write_file(artifact / "repair_agent" / "agent.py")
    write_file(artifact / "paper" / "repair_agent.pdf")

    manifest = prepare_dataset(artifact, output, dry_run=True)

    assert manifest_summary(manifest) == (
        "source_root: "
        f"{artifact.resolve()}\n"
        "output_root: "
        f"{output.resolve()}\n"
        "copied_count: 0\n"
        "skipped_count: 2\n"
        "copied_examples:\n"
        "skipped_examples:\n"
        "- paper/repair_agent.pdf\n"
        "- repair_agent/agent.py"
    )
