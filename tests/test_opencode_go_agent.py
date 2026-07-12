import importlib.util
import sys
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "agents" / "opencode_go" / "run.py"
SPEC = importlib.util.spec_from_file_location("opencode_go_agent_run", MODULE_PATH)
assert SPEC is not None
opencode_go_agent = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = opencode_go_agent
SPEC.loader.exec_module(opencode_go_agent)


def test_build_client_uses_opencode_go_base_url(monkeypatch) -> None:
    calls: list[dict[str, str]] = []

    class FakeOpenAI:
        def __init__(self, api_key: str, base_url: str) -> None:
            calls.append({"api_key": api_key, "base_url": base_url})

    monkeypatch.setattr(opencode_go_agent, "OpenAI", FakeOpenAI)

    opencode_go_agent.build_client("go-key")

    assert calls == [
        {
            "api_key": "go-key",
            "base_url": "https://opencode.ai/zen/go/v1",
        }
    ]


def test_build_client_rejects_missing_key() -> None:
    try:
        opencode_go_agent.build_client("")
    except ValueError as error:
        assert "OPENCODE_API_KEY" in str(error)
    else:
        raise AssertionError("build_client should reject missing OPENCODE_API_KEY")


def test_sandbox_env_contains_only_opencode_key_for_paid_model_access() -> None:
    content = opencode_go_agent.sandbox_env_content(
        {
            "OPENCODE_API_KEY": "go-key",
            "OPENAI_API_KEY": "should-not-copy",
            "ANTHROPIC_API_KEY": "should-not-copy",
            "GOOGLE_API_KEY": "should-not-copy",
            "HF_TOKEN": "should-not-copy",
        }
    )

    assert "OPENCODE_API_KEY=go-key" in content
    assert "OPENAI_API_KEY=\n" in content
    assert "ANTHROPIC_API_KEY=\n" in content
    assert "GOOGLE_API_KEY=\n" in content
    assert "HF_TOKEN=\n" in content


def test_copy_task_data_uses_requested_collection(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(opencode_go_agent, "MAIN_PATH", tmp_path)
    data_dir = tmp_path / "benchmark" / "papers_se" / "repair_agent_program_repair" / "data"
    data_dir.mkdir(parents=True)
    (data_dir / "sample.txt").write_text("sample\n", encoding="utf-8")

    sandbox = tmp_path / "sandbox"
    opencode_go_agent.copy_task_data(
        "repair_agent_program_repair",
        "",
        sandbox,
        collection="papers_se",
    )

    assert (sandbox / "sample.txt").read_text(encoding="utf-8") == "sample\n"
