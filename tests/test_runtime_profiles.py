import importlib.util
import json
import sys
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "check_runtime_profile.py"
SPEC = importlib.util.spec_from_file_location("check_runtime_profile", MODULE_PATH)
assert SPEC is not None
runtime_profiles = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = runtime_profiles
SPEC.loader.exec_module(runtime_profiles)

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_se_java_defects4j_profile_defines_the_common_repair_runtime_tools() -> None:
    profile = json.loads((REPO_ROOT / "runtime-profiles" / "se_java_defects4j.json").read_text(encoding="utf-8"))

    assert profile["id"] == "se-java-defects4j"
    assert set(profile["required_commands"]) >= {
        "java",
        "perl",
        "git",
        "patch",
        "mvn",
        "ant",
        "defects4j",
    }


def test_runtime_profile_check_reports_missing_commands_without_installing_them(tmp_path: Path) -> None:
    profile_dir = tmp_path / "runtime-profiles"
    profile_dir.mkdir()
    (profile_dir / "sample_profile.json").write_text(
        json.dumps(
            {
                "id": "sample-profile",
                "required_commands": ["java", "defects4j"],
                "required_environment": ["DEFECTS4J_HOME"],
            }
        ),
        encoding="utf-8",
    )

    result = runtime_profiles.check_runtime_profile(
        "sample-profile",
        profile_dir=profile_dir,
        which=lambda command: f"/bin/{command}" if command == "java" else None,
        environ={},
    )

    assert not result.ok
    assert result.missing_commands == ("defects4j",)
    assert result.missing_environment == ("DEFECTS4J_HOME",)
    assert "sample-profile" in result.message()
