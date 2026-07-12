from __future__ import annotations

import json
import os
import random
import shutil
import subprocess
import sys
import textwrap
import time
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.check_runtime_profile import (  # noqa: E402
    RuntimePreflightResult,
    check_runtime_profile,
    runtime_profile_for_task,
)

load_dotenv()

MAIN_PATH = Path.cwd()
DEFAULT_COLLECTION = "papers"
DEFAULT_CODEX_BIN = "codex"
DEFAULT_CODEX_SANDBOX = "workspace-write"
RUNTIME_CHECK_DISABLED_VALUES = {"0", "false", "False", "no", "NO"}


def sandbox_env_content() -> str:
    return "\n".join(
        [
            "OPENAI_API_KEY=",
            "ANTHROPIC_API_KEY=",
            "GOOGLE_API_KEY=",
            "HF_TOKEN=",
            "OPENCODE_API_KEY=",
            "",
        ]
    )


def sandbox_git_config_content() -> str:
    return "\n".join(
        [
            "[user]",
            "\tname = FIRE-Bench",
            "\temail = fire-bench@example.invalid",
            "[commit]",
            "\tgpgsign = false",
            "[tag]",
            "\tgpgsign = false",
            "",
        ]
    )


def codex_agent_environment(sandbox: Path) -> dict[str, str]:
    env = os.environ.copy()
    env.update(
        {
            "GIT_CONFIG_GLOBAL": str(sandbox / ".gitconfig"),
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_AUTHOR_NAME": "FIRE-Bench",
            "GIT_AUTHOR_EMAIL": "fire-bench@example.invalid",
            "GIT_COMMITTER_NAME": "FIRE-Bench",
            "GIT_COMMITTER_EMAIL": "fire-bench@example.invalid",
        }
    )
    return env


def copy_task_data(
    task_id: str,
    figure_id: str,
    sandbox: Path,
    collection: str = DEFAULT_COLLECTION,
) -> None:
    data_dir = (
        MAIN_PATH / "benchmark" / collection / task_id / figure_id / "data"
        if figure_id
        else MAIN_PATH / "benchmark" / collection / task_id / "data"
    )
    if data_dir.exists() and any(data_dir.iterdir()):
        shutil.copytree(data_dir, sandbox)
        return
    sandbox.mkdir(parents=True, exist_ok=True)


def instruction_dir_for_task(
    task_id: str,
    figure_id: str,
    collection: str = DEFAULT_COLLECTION,
) -> Path:
    path = MAIN_PATH / "benchmark" / collection / task_id
    if figure_id:
        path = path / figure_id
    return path


def sandbox_file_listing(sandbox: Path) -> str:
    files = []
    for path in sorted(sandbox.rglob("*")):
        if path.is_file() and ".env" not in path.name:
            files.append(str(path.relative_to(sandbox)))
    return "\n".join(files[:80]) or "(empty)"


def build_agent_prompt(instruction_text: str, sandbox: Path) -> str:
    return textwrap.dedent(
        f"""\
        You are running as an autonomous Codex CLI research agent.
        Use the files and command-line tools in the working directory to run the requested experiments.
        Do not use web search.
        Do not read files outside the working directory unless the task explicitly permits it.
        When finished, provide the final research conclusions in your last response.

        ## Research Task

        {instruction_text}

        ## Working Directory

        {sandbox}

        ## Files Available

        ```
        {sandbox_file_listing(sandbox)}
        ```
        """
    ).strip()


def build_codex_command(
    *,
    codex_bin: str,
    model: str,
    sandbox: Path,
    last_message_file: Path,
    sandbox_mode: str,
) -> list[str]:
    return [
        codex_bin,
        "--ask-for-approval",
        "never",
        "exec",
        "--model",
        model,
        "--sandbox",
        sandbox_mode,
        "--ignore-user-config",
        "--cd",
        str(sandbox),
        "--add-dir",
        str(sandbox / "utils"),
        "--skip-git-repo-check",
        "--ephemeral",
        "--json",
        "--output-last-message",
        str(last_message_file),
        "-",
    ]


def write_log_header(log_file: Path, agent_id: str, task_id: str, model: str, collection: str) -> None:
    log_file.parent.mkdir(parents=True, exist_ok=True)
    log_file.write_text(
        "\n".join(
            [
                f"agent_id: {agent_id}",
                f"task_id: {task_id}",
                f"collection: {collection}",
                f"llm_model: {model}",
                "=" * 40,
                "",
            ]
        ),
        encoding="utf-8",
    )


def append_result(log_file: Path, result: str, return_code: int) -> None:
    with log_file.open("a", encoding="utf-8") as stream:
        stream.write(f"\n{'=' * 40}\n")
        stream.write(f"return_code: {return_code}\n")
        stream.write(f"result: {result}\n")
        stream.write(json.dumps({"result": result, "return_code": return_code}, ensure_ascii=False))
        stream.write("\n")


def runtime_profile_checks_enabled() -> bool:
    return os.environ.get("CHECK_RUNTIME_PROFILE", "1") not in RUNTIME_CHECK_DISABLED_VALUES


def maybe_append_runtime_preflight_failure(
    log_file: Path,
    result: RuntimePreflightResult,
) -> bool:
    if result.ok:
        return False

    append_result(log_file, result.message(), 125)
    return True


def run_codex_agent(
    *,
    command: list[str],
    prompt: str,
    sandbox: Path,
    log_file: Path,
) -> int:
    with log_file.open("a", encoding="utf-8") as stream:
        process = subprocess.run(
            command,
            cwd=sandbox,
            input=prompt,
            stdout=stream,
            stderr=subprocess.STDOUT,
            text=True,
            env=codex_agent_environment(sandbox),
        )
    return process.returncode


def main() -> None:
    agent_id = os.environ.get("AGENT_ID", "codex")
    task_id = os.environ.get("TASK_ID", "")
    figure_id = os.environ.get("FIGURE_ID", "")
    collection = os.environ.get("COLLECTION", DEFAULT_COLLECTION)
    model = os.environ.get("LLM_MODEL", "gpt-5.3-codex")
    codex_bin = os.environ.get("CODEX_BIN", DEFAULT_CODEX_BIN)
    sandbox_mode = os.environ.get("CODEX_SANDBOX", DEFAULT_CODEX_SANDBOX)

    timestamp = time.strftime("%Y%m%d%H%M%S")
    run_id = random.randint(10000, 99999)
    sandbox = MAIN_PATH / "runs" / f"{agent_id}_{model.replace('/', '-')}_{timestamp}_{run_id}"
    task_root = instruction_dir_for_task(task_id, figure_id, collection)
    log_file = MAIN_PATH / "log" / agent_id / model / task_id / f"{timestamp}_{run_id}" / "log.log"
    last_message_file = log_file.parent / "last_message.txt"
    write_log_header(log_file, agent_id, task_id, model, collection)

    runtime_profile = runtime_profile_for_task(task_root)
    if runtime_profile and runtime_profile_checks_enabled():
        preflight_result = check_runtime_profile(runtime_profile)
        if maybe_append_runtime_preflight_failure(log_file, preflight_result):
            print(f"Run skipped. {preflight_result.message()} Logs saved to {log_file}")
            return

    copy_task_data(task_id, figure_id, sandbox, collection)
    shutil.copytree(MAIN_PATH / "utils", sandbox / "utils")
    (sandbox / ".env").write_text(sandbox_env_content(), encoding="utf-8")
    (sandbox / ".gitconfig").write_text(sandbox_git_config_content(), encoding="utf-8")

    instruction_file = task_root / "instruction" / "instruction.txt"
    instruction_text = instruction_file.read_text(encoding="utf-8").strip()
    prompt = build_agent_prompt(instruction_text, sandbox)

    command = build_codex_command(
        codex_bin=codex_bin,
        model=model,
        sandbox=sandbox,
        last_message_file=last_message_file,
        sandbox_mode=sandbox_mode,
    )
    return_code = run_codex_agent(
        command=command,
        prompt=prompt,
        sandbox=sandbox,
        log_file=log_file,
    )
    result = (
        last_message_file.read_text(encoding="utf-8").strip()
        if last_message_file.exists()
        else f"Codex CLI exited without writing a final message. exit_code={return_code}"
    )
    append_result(log_file, result, return_code)

    print(f"Run complete. Logs saved to {log_file}")


if __name__ == "__main__":
    main()
