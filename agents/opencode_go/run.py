from __future__ import annotations

import json
import os
import random
import re
import shutil
import subprocess
import sys
import textwrap
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

MAIN_PATH = Path.cwd()
OPENCODE_GO_BASE_URL = "https://opencode.ai/zen/go/v1"
MAX_TURNS = 30
CODE_TIMEOUT_SECONDS = 300

SYSTEM_PROMPT = textwrap.dedent(
    """\
    You are an autonomous research agent. You are given a research task with instructions.
    You have a working directory with data files and utility scripts.
    You must write and execute Python code to carry out experiments.

    RULES:
    - Write Python code in ```python ... ``` blocks. Each block will be executed immediately.
    - Do not install paid API clients or call non-OpenCode model providers.
    - Use only LLMInference(provider="opencode_go", model_name=...) for model calls.
    - Iterate: analyze results, fix errors, run more experiments.
    - When you are done, write your final conclusions in a block starting with "FINAL CONCLUSION:".
    - Be concise. Focus on running experiments and producing quantitative results.
    - The working directory contains a .env file with OPENCODE_API_KEY and a utils/ folder.
    - Do NOT use web search. Run experiments from the data provided.
    """
)


def build_client(api_key: str) -> OpenAI:
    if not api_key:
        raise ValueError("OPENCODE_API_KEY is required for the OpenCode Go outer agent")
    return OpenAI(api_key=api_key, base_url=OPENCODE_GO_BASE_URL)


def sandbox_env_content(env: dict[str, str]) -> str:
    return "\n".join(
        [
            f"OPENCODE_API_KEY={env.get('OPENCODE_API_KEY', '')}",
            "OPENAI_API_KEY=",
            "ANTHROPIC_API_KEY=",
            "GOOGLE_API_KEY=",
            "HF_TOKEN=",
            "",
        ]
    )


def extract_code_blocks(text: str) -> list[str]:
    pattern = r"```python\s*\n(.*?)```"
    return re.findall(pattern, text, re.DOTALL)


def extract_conclusion(text: str) -> str | None:
    if "FINAL CONCLUSION:" not in text:
        return None
    return text.split("FINAL CONCLUSION:", 1)[1].strip()


def run_code(code: str, cwd: Path, env: dict[str, str]) -> str:
    try:
        result = subprocess.run(
            [sys.executable, "-c", code],
            cwd=str(cwd),
            env=env,
            capture_output=True,
            text=True,
            timeout=CODE_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return "ERROR: Code execution timed out after 5 minutes."
    except Exception as error:
        return f"ERROR: {error}"

    output = ""
    if result.stdout:
        output += result.stdout
    if result.stderr:
        output += "\nSTDERR:\n" + result.stderr
    if len(output) > 8000:
        output = output[:4000] + "\n... [truncated] ...\n" + output[-4000:]
    return output.strip() or "(no output)"


def copy_task_data(task_id: str, figure_id: str, sandbox: Path) -> None:
    instances_src = (
        MAIN_PATH / f"benchmark/papers/{task_id}/{figure_id}/data"
        if figure_id
        else MAIN_PATH / f"benchmark/papers/{task_id}/data"
    )
    if instances_src.exists() and any(instances_src.iterdir()):
        shutil.copytree(instances_src, sandbox)
        return
    sandbox.mkdir(parents=True, exist_ok=True)


def sandbox_file_listing(sandbox: Path) -> str:
    files = []
    for path in sorted(sandbox.rglob("*")):
        if path.is_file() and ".env" not in path.name:
            files.append(str(path.relative_to(sandbox)))
    return "\n".join(files[:50]) or "(empty)"


def completion_kwargs(model: str, messages: list[dict[str, str]]) -> dict[str, object]:
    return {
        "model": model,
        "messages": messages,
        "max_tokens": 4096,
        "temperature": 0,
    }


def main() -> None:
    agent_id = os.environ.get("AGENT_ID", "opencode_go")
    task_id = os.environ.get("TASK_ID", "")
    figure_id = os.environ.get("FIGURE_ID", "")
    model = os.environ.get("LLM_MODEL", "deepseek-v4-pro")
    opencode_key = os.environ.get("OPENCODE_API_KEY", "")

    timestamp = time.strftime("%Y%m%d%H%M%S")
    run_id = random.randint(10000, 99999)

    sandbox = MAIN_PATH / "runs" / f"{agent_id}_{model.replace('/', '-')}_{timestamp}_{run_id}"
    copy_task_data(task_id, figure_id, sandbox)
    shutil.copytree(MAIN_PATH / "utils", sandbox / "utils")
    (sandbox / ".env").write_text(sandbox_env_content(os.environ), encoding="utf-8")

    instruction_dir = MAIN_PATH / "benchmark" / "papers" / task_id
    if figure_id:
        instruction_dir = instruction_dir / figure_id
    instruction_file = instruction_dir / "instruction" / "instruction.txt"
    instruction_text = instruction_file.read_text(encoding="utf-8").strip()

    log_file = MAIN_PATH / "log" / agent_id / model / task_id / f"{timestamp}_{run_id}" / "log.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)

    exec_env = os.environ.copy()
    exec_env["OPENCODE_API_KEY"] = opencode_key
    exec_env["OPENAI_API_KEY"] = ""
    exec_env["ANTHROPIC_API_KEY"] = ""
    exec_env["GOOGLE_API_KEY"] = ""
    exec_env["HF_TOKEN"] = ""

    client = build_client(opencode_key)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"## Research Task\n\n{instruction_text}\n\n"
                f"## Working Directory\nYour working directory is: {sandbox}\n\n"
                f"## Files Available\n```\n{sandbox_file_listing(sandbox)}\n```\n\n"
                "Begin your research. Write Python code to execute experiments."
            ),
        },
    ]
    log_lines = [
        f"agent_id: {agent_id}",
        f"task_id: {task_id}",
        f"llm_model: {model}",
        "=" * 40,
    ]

    conclusion = None
    for turn in range(MAX_TURNS):
        print(f"  [{task_id}] OpenCode Go turn {turn + 1}/{MAX_TURNS} ...")
        try:
            response = client.chat.completions.create(**completion_kwargs(model, messages))
            assistant_message = response.choices[0].message.content or ""
        except Exception as error:
            assistant_message = f"API ERROR: {error}"
            log_lines.append(f"\n--- TURN {turn + 1} (API ERROR) ---\n{assistant_message}")
            break

        messages.append({"role": "assistant", "content": assistant_message})
        log_lines.append(f"\n--- TURN {turn + 1} (ASSISTANT) ---\n{assistant_message}")

        conclusion = extract_conclusion(assistant_message)
        if conclusion:
            log_lines.append(f"\n--- FINAL CONCLUSION ---\n{conclusion}")
            break

        code_blocks = extract_code_blocks(assistant_message)
        if not code_blocks:
            messages.append(
                {
                    "role": "user",
                    "content": "Please write Python code to run experiments, or provide your FINAL CONCLUSION: if done.",
                }
            )
            continue

        outputs = []
        for index, code in enumerate(code_blocks):
            output = run_code(code, sandbox, exec_env)
            outputs.append(f"[Code block {index + 1} output]\n{output}")
            log_lines.append(f"\n--- CODE BLOCK {index + 1} ---\n{code}\n--- OUTPUT ---\n{output}")
        messages.append({"role": "user", "content": "Execution results:\n\n" + "\n\n".join(outputs)})

    if not conclusion:
        messages.append({"role": "user", "content": "Time is up. Provide your FINAL CONCLUSION: now."})
        try:
            response = client.chat.completions.create(**completion_kwargs(model, messages))
            final = response.choices[0].message.content or ""
            conclusion = extract_conclusion(final) or final
            log_lines.append(f"\n--- FORCED FINAL ---\n{final}")
        except Exception as error:
            conclusion = f"Failed to get conclusion: {error}"

    log_lines.append(f"\n{'=' * 40}\nresult: {conclusion}")
    log_lines.append(json.dumps({"result": conclusion}))
    log_file.write_text("\n".join(log_lines), encoding="utf-8")

    print(f"  [{task_id}] Done. Log: {log_file}")


if __name__ == "__main__":
    main()
