import importlib.util
import sys
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "agents" / "codex" / "run.py"
SPEC = importlib.util.spec_from_file_location("codex_agent_run", MODULE_PATH)
assert SPEC is not None
codex_agent = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = codex_agent
SPEC.loader.exec_module(codex_agent)


def test_sandbox_env_does_not_copy_host_api_keys() -> None:
    content = codex_agent.sandbox_env_content()

    assert "OPENAI_API_KEY=\n" in content
    assert "ANTHROPIC_API_KEY=\n" in content
    assert "GOOGLE_API_KEY=\n" in content
    assert "HF_TOKEN=\n" in content
    assert "OPENCODE_API_KEY=\n" in content


def test_sandbox_git_config_disables_host_signing() -> None:
    content = codex_agent.sandbox_git_config_content()

    assert "name = FIRE-Bench" in content
    assert "email = fire-bench@example.invalid" in content
    assert "gpgsign = false" in content


def test_codex_agent_environment_uses_sandbox_git_config(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", "/host/.gitconfig")
    monkeypatch.setenv("GIT_AUTHOR_NAME", "Host User")
    sandbox = tmp_path / "sandbox"

    env = codex_agent.codex_agent_environment(sandbox)

    assert env["GIT_CONFIG_GLOBAL"] == str(sandbox / ".gitconfig")
    assert env["GIT_CONFIG_NOSYSTEM"] == "1"
    assert env["GIT_AUTHOR_NAME"] == "FIRE-Bench"
    assert env["GIT_AUTHOR_EMAIL"] == "fire-bench@example.invalid"
    assert env["GIT_COMMITTER_NAME"] == "FIRE-Bench"
    assert env["GIT_COMMITTER_EMAIL"] == "fire-bench@example.invalid"


def test_copy_task_data_uses_requested_collection(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(codex_agent, "MAIN_PATH", tmp_path)
    data_dir = tmp_path / "benchmark" / "papers_se" / "repair_agent_program_repair" / "data"
    data_dir.mkdir(parents=True)
    (data_dir / "sample.txt").write_text("sample\n", encoding="utf-8")

    sandbox = tmp_path / "sandbox"
    codex_agent.copy_task_data(
        "repair_agent_program_repair",
        "",
        sandbox,
        collection="papers_se",
    )

    assert (sandbox / "sample.txt").read_text(encoding="utf-8") == "sample\n"


def test_build_agent_prompt_frames_codex_as_an_autonomous_agent(tmp_path: Path) -> None:
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir()
    (sandbox / "data.txt").write_text("data\n", encoding="utf-8")

    prompt = codex_agent.build_agent_prompt("Answer the research question.", sandbox)

    assert "autonomous Codex CLI research agent" in prompt
    assert "Answer the research question." in prompt
    assert "data.txt" in prompt
    assert "Do not use web search." in prompt


def test_build_codex_command_invokes_exec_agent_with_stdin_prompt(tmp_path: Path) -> None:
    sandbox = tmp_path / "sandbox"
    last_message = tmp_path / "log" / "last_message.txt"

    command = codex_agent.build_codex_command(
        codex_bin="codex",
        model="gpt-5.3-codex",
        sandbox=sandbox,
        last_message_file=last_message,
        sandbox_mode="workspace-write",
    )

    assert command == [
        "codex",
        "--ask-for-approval",
        "never",
        "exec",
        "--model",
        "gpt-5.3-codex",
        "--sandbox",
        "workspace-write",
        "--ignore-user-config",
        "--cd",
        str(sandbox),
        "--add-dir",
        str(sandbox / "utils"),
        "--skip-git-repo-check",
        "--ephemeral",
        "--json",
        "--output-last-message",
        str(last_message),
        "-",
    ]


def test_build_codex_command_only_adds_sandbox_utils(tmp_path: Path) -> None:
    sandbox = tmp_path / "sandbox"
    last_message = tmp_path / "log" / "last_message.txt"

    command = codex_agent.build_codex_command(
        codex_bin="codex",
        model="gpt-5.5",
        sandbox=sandbox,
        last_message_file=last_message,
        sandbox_mode="workspace-write",
    )

    assert command.count("--add-dir") == 1
    assert str(sandbox / "utils") in command


def test_append_result_writes_eval_compatible_json_line(tmp_path: Path) -> None:
    log_file = tmp_path / "log.log"
    log_file.write_text("header\n", encoding="utf-8")

    codex_agent.append_result(log_file, "final claims", 0)

    content = log_file.read_text(encoding="utf-8")
    assert "result: final claims" in content
    assert '{"result": "final claims", "return_code": 0}' in content


def test_runtime_profile_preflight_skips_agent_execution_when_required_tools_are_missing(
    tmp_path: Path,
) -> None:
    log_file = tmp_path / "log.log"
    log_file.write_text("header\n", encoding="utf-8")
    profile_result = codex_agent.RuntimePreflightResult(
        ok=False,
        profile_id="se-java-defects4j",
        missing_commands=("defects4j",),
        missing_environment=(),
    )

    executed = codex_agent.maybe_append_runtime_preflight_failure(
        log_file,
        profile_result,
    )

    assert executed is True
    assert "Infrastructure failure" in log_file.read_text(encoding="utf-8")
