from pathlib import Path

TASK_ROOT = Path("benchmark/papers_se/repair_agent_program_repair")


def test_repair_agent_task_declares_the_se_java_defects4j_runtime_profile() -> None:
    task_config = (TASK_ROOT / "task_config.yaml").read_text(encoding="utf-8")

    assert "runtime_profile: se-java-defects4j" in task_config


def test_repair_agent_visible_task_requires_repository_driven_reproduction() -> None:
    instruction = (TASK_ROOT / "instruction" / "instruction.txt").read_text(encoding="utf-8")

    assert "data/repair_agent_artifact/" in instruction
    assert "replay_repair_agent_sample.py" in instruction
    assert "reconstruct_repair_agent_aggregate.py" in instruction
    assert "repository-driven reproduction task" in instruction
    assert "structured evidence" not in instruction.lower()
    assert "data/repair_agent_evidence" not in instruction


def test_repair_agent_visible_data_includes_released_aggregate_inputs_without_hidden_answers() -> None:
    data_readme = (TASK_ROOT / "data" / "README.md").read_text(encoding="utf-8")
    artifact = TASK_ROOT / "data" / "repair_agent_artifact"

    assert not (TASK_ROOT / "data" / "repair_agent_evidence").exists()
    assert (TASK_ROOT / "data" / "replay_repair_agent_sample.py").exists()
    assert (TASK_ROOT / "data" / "reconstruct_repair_agent_aggregate.py").exists()
    assert (artifact / "data" / "final_list_of_fixed_bugs").exists()
    assert (artifact / "data" / "fixes_implementation").exists()
    assert (artifact / "repair_agent" / "experimental_setups" / "generate_main_table.py").exists()
    assert (artifact / "repair_agent" / "experimental_setups" / "draw_venn_chatrepair_clean.py").exists()
    assert "released aggregate reconstruction inputs" in data_readme
    assert "GitBug-Java execution results" in data_readme
    assert "Failing tests: 0" in data_readme


def test_repair_agent_task_does_not_require_runner_specific_runtime_wrapper() -> None:
    instruction = (TASK_ROOT / "instruction" / "instruction.txt").read_text(encoding="utf-8")
    data_readme = (TASK_ROOT / "data" / "README.md").read_text(encoding="utf-8")

    assert "REPAIR_AGENT_RUNTIME_IMAGE" not in instruction
    assert "utils/repair_agent_docker.sh" not in instruction
    assert "setup_repair_agent_toolchain.sh" not in data_readme
    assert "nix develop" not in data_readme
