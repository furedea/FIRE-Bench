from pathlib import Path


def test_run_opencode_go_subset_script_targets_five_tasks() -> None:
    script = Path("scripts/run_opencode_go_subset.sh").read_text(encoding="utf-8")

    assert 'readonly OUTER_AGENT_ID="opencode_go"' in script
    assert '"questbench"' in script
    assert '"counterfactual_simulatability"' in script
    assert '"cot_in_planning"' in script
    assert '"awareness_detection"' in script
    assert '"llms_assume_rationality"' in script


def test_run_opencode_go_subset_script_evaluates_with_opencode_go() -> None:
    script = Path("scripts/run_opencode_go_subset.sh").read_text(encoding="utf-8")

    assert "python eval/opencode_go_eval.py" in script
    assert '--judge-model "${JUDGE_MODEL}"' in script
    assert '--repair-model "${REPAIR_MODEL}"' in script
    assert 'readonly JUDGE_MODEL="${JUDGE_MODEL:-qwen3.6-plus}"' in script
