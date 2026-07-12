import importlib.util
import sys
from pathlib import Path

MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "benchmark"
    / "papers_se"
    / "repair_agent_program_repair"
    / "data"
    / "replay_repair_agent_sample.py"
)
SPEC = importlib.util.spec_from_file_location("repair_agent_sample_replay", MODULE_PATH)
assert SPEC is not None
sample_replay = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = sample_replay
SPEC.loader.exec_module(sample_replay)


def test_defects4j_output_with_zero_failing_tests_is_plausible_even_when_return_code_is_nonzero() -> None:
    result = sample_replay.parse_defects4j_test_result(
        return_code=1,
        stdout="Running ant...\nFailing tests: 0\n",
        stderr="",
    )

    assert result.failing_tests == 0
    assert result.plausible is True


def test_defects4j_output_with_failing_tests_is_not_plausible_even_when_return_code_is_zero() -> None:
    result = sample_replay.parse_defects4j_test_result(
        return_code=0,
        stdout="Running ant...\nFailing tests: 1\n  - org.example.Test::test_bug\n",
        stderr="",
    )

    assert result.failing_tests == 1
    assert result.plausible is False


def test_bounded_candidate_selection_limits_each_bug_independently(tmp_path: Path) -> None:
    artifact_root = tmp_path / "repair_agent_artifact"
    patch_dir = artifact_root / "data" / "derivated_patches"
    patch_dir.mkdir(parents=True)
    (patch_dir / "experiment_001mutants_Chart_1.json").write_text(
        '[{"file_name":"A.java","insertions":[],"deletions":[],"modifications":[]}]\n',
        encoding="utf-8",
    )
    (patch_dir / "experiment_002mutants_Chart_1.json").write_text(
        '[{"file_name":"B.java","insertions":[],"deletions":[],"modifications":[]}]\n',
        encoding="utf-8",
    )
    (patch_dir / "experiment_001mutants_Lang_1.json").write_text(
        '[{"file_name":"C.java","insertions":[],"deletions":[],"modifications":[]}]\n',
        encoding="utf-8",
    )
    bugs = (
        sample_replay.Defects4JBug(project="Chart", bug_id=1),
        sample_replay.Defects4JBug(project="Lang", bug_id=1),
    )

    candidates = sample_replay.collect_candidates(
        artifact_root=artifact_root,
        bugs=bugs,
        max_candidates_per_bug=1,
    )

    assert [candidate.bug.key for candidate in candidates] == ["Chart-1", "Lang-1"]
    assert [candidate.candidate_order for candidate in candidates] == [0, 0]


def test_candidate_selection_skips_unparseable_artifact_files(tmp_path: Path) -> None:
    artifact_root = tmp_path / "repair_agent_artifact"
    patch_dir = artifact_root / "data" / "derivated_patches"
    patch_dir.mkdir(parents=True)
    (patch_dir / "experiment_001mutants_Chart_1.json").write_text(
        "{not parseable",
        encoding="utf-8",
    )
    (patch_dir / "experiment_002mutants_Chart_1.json").write_text(
        '[{"file_name":"A.java","insertions":[],"deletions":[],"modifications":[]}]\n',
        encoding="utf-8",
    )

    candidates = sample_replay.collect_candidates(
        artifact_root=artifact_root,
        bugs=(sample_replay.Defects4JBug(project="Chart", bug_id=1),),
        max_candidates_per_bug=1,
    )

    assert len(candidates) == 1
    assert candidates[0].source_path.name == "experiment_002mutants_Chart_1.json"


def test_prompt_response_candidate_files_are_parsed(tmp_path: Path) -> None:
    path = tmp_path / "experiment_001mutants_Chart_1.json"
    path.write_text(
        repr(
            {
                "prompt": "Generate mutants",
                "response": (
                    '[{"file_name":"A.java","insertions":[],"deletions":[],'
                    '"modifications":[{"line_number":1,"modified_line":"class A {}"}]}]'
                ),
            }
        ),
        encoding="utf-8",
    )

    candidates = sample_replay.load_candidate_changes(path)

    assert candidates[0][0]["file_name"] == "A.java"


def test_bug_argument_filters_loaded_bug_sample() -> None:
    bugs = (
        sample_replay.Defects4JBug(project="Chart", bug_id=1),
        sample_replay.Defects4JBug(project="Lang", bug_id=1),
    )

    selected = sample_replay.select_bugs(bugs, ("Lang-1",))

    assert selected == (sample_replay.Defects4JBug(project="Lang", bug_id=1),)
