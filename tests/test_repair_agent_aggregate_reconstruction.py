import importlib.util
import sys
from pathlib import Path

MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "benchmark"
    / "papers_se"
    / "repair_agent_program_repair"
    / "data"
    / "reconstruct_repair_agent_aggregate.py"
)
SPEC = importlib.util.spec_from_file_location("repair_agent_aggregate_reconstruction", MODULE_PATH)
assert SPEC is not None
aggregate = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = aggregate
SPEC.loader.exec_module(aggregate)


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_summary_reconstructs_counts_from_released_artifact_inputs(tmp_path: Path) -> None:
    artifact = tmp_path / "repair_agent_artifact"
    write_file(
        artifact / "data" / "final_list_of_fixed_bugs",
        "Chart 1\nClosure 140\nCompress 2\n",
    )
    write_file(
        artifact / "data" / "fixes_implementation",
        """# Chart 1
## Fix:
{'file_name': 'A.java', 'modifications': [{'line_number': 1, 'modified_line': 'x'}]}
## Why:
Identical.

# Closure 140
## Fix:
{'file_name': 'B.java', 'modifications': [{'line_number': 2, 'modified_line': 'y'}]}
## Why:
Semantically equivalent.

# Compress 2
## Fix:
{'file_name': 'C.java', 'insertions': [{'line_number': 3, 'new_lines': ['z']}]}
## Why:
Good enough.
""",
    )
    write_file(
        artifact / "repair_agent" / "experimental_setups" / "generate_main_table.py",
        '''self_apr = """Chart 1
Closure 140
Closure 140""".replace("\\n\\n", "\\n")
chatgpt_fixes = """Chart-1.java
Lang-2.java""".replace(".java", "").replace("-", " ")
iterlist = """Closure 140
Math 3"""
repair_agent_list = """Chart 1
Closure 140
Compress 2"""
total_bugs = {"Chart": 2, "Closure": 3, "Compress": 4}
plausibles = {"Chart": 1, "Closure": 2, "Compress": 1}
''',
    )
    write_file(
        artifact / "repair_agent" / "experimental_setups" / "gitbuglist",
        "repo-a-abc\nrepo-b-def\nrepo-b-def\n",
    )

    summary = aggregate.build_summary(artifact)

    assert summary["defects4j"]["total_bugs"] == 9
    assert summary["repair_agent"]["correct_total"] == 3
    assert summary["repair_agent"]["plausible_manual_analysis_total"] == 4
    assert summary["repair_agent"]["version_split"]["legacy_defects4j_projects"] == 1
    assert summary["repair_agent"]["version_split"]["additional_defects4j_2_projects"] == 2
    assert summary["baselines"]["ChatRepair"]["unique_total"] == 2
    assert summary["baselines"]["ITER"]["unique_total"] == 2
    assert summary["baselines"]["SelfAPR"]["raw_total"] == 3
    assert summary["repair_agent"]["exclusive_vs_compared_baselines"]["count"] == 1
    assert summary["manual_review_labels"]["counts"] == {
        "good_enough": 1,
        "identical": 1,
        "semantically_equivalent": 1,
    }
    assert summary["gitbug_java"]["sample_total"] == 3
    assert summary["gitbug_java"]["unique_sample_total"] == 2


def test_bug_ids_are_normalized_across_spaces_dashes_underscores_and_java_suffixes() -> None:
    bugs = aggregate.parse_bug_lines(("Chart 1", "Cli-11.java", "JacksonCore_25", ""))

    assert bugs == ("Chart-1", "Cli-11", "JacksonCore-25")
