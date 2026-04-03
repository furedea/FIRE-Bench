"""
Simple agentic runner: reads instruction, uses OpenAI Chat Completions API
in a code-generation + execution loop until the agent produces conclusions.
Drop-in replacement for codex/openhands runners.
"""
import subprocess
import os
import sys
import time
import random
import json
import re
import textwrap
from pathlib import Path
import shutil
from dotenv import load_dotenv

load_dotenv()

Main_Path = Path.cwd()

SYSTEM_PROMPT = textwrap.dedent("""\
You are an autonomous research agent. You are given a research task with instructions.
You have a working directory with data files and utility scripts.
You must write and execute Python code to carry out experiments.

RULES:
- Write Python code in ```python ... ``` blocks. Each block will be executed immediately.
- You can install packages with pip if needed.
- After each code execution you will see stdout/stderr output.
- Iterate: analyze results, fix errors, run more experiments.
- When you are done, write your final conclusions in a block starting with "FINAL CONCLUSION:".
- Be concise. Focus on running experiments and producing quantitative results.
- The working directory contains a .env file with API keys and a utils/ folder.
- Do NOT use web search. Run FULL experiments from the data provided.
""")

MAX_TURNS = 30
CODE_TIMEOUT = 300  # 5 min per code block


def extract_code_blocks(text):
    """Extract python code blocks from markdown."""
    pattern = r'```python\s*\n(.*?)```'
    return re.findall(pattern, text, re.DOTALL)


def extract_conclusion(text):
    """Check if text contains FINAL CONCLUSION."""
    if "FINAL CONCLUSION:" in text:
        return text.split("FINAL CONCLUSION:", 1)[1].strip()
    return None


def run_code(code, cwd, env):
    """Execute a Python code string and return stdout+stderr."""
    try:
        result = subprocess.run(
            [sys.executable, "-c", code],
            cwd=str(cwd),
            env=env,
            capture_output=True,
            text=True,
            timeout=CODE_TIMEOUT,
        )
        output = ""
        if result.stdout:
            output += result.stdout
        if result.stderr:
            output += "\nSTDERR:\n" + result.stderr
        # Truncate very long outputs
        if len(output) > 8000:
            output = output[:4000] + "\n... [truncated] ...\n" + output[-4000:]
        return output.strip() or "(no output)"
    except subprocess.TimeoutExpired:
        return "ERROR: Code execution timed out after 5 minutes."
    except Exception as e:
        return f"ERROR: {e}"


def main():
    from openai import OpenAI

    agent_id = os.environ.get("AGENT_ID", "simple")
    task_id = os.environ.get("TASK_ID", "")
    figure_id = os.environ.get("FIGURE_ID", "")
    LLM_MODEL = os.environ.get("LLM_MODEL", "gpt-5")

    timestamp = time.strftime("%Y%m%d%H%M%S")
    rd = random.randint(10000, 99999)

    # Setup sandbox
    run_dir = Main_Path / "runs"
    run_dir.mkdir(parents=True, exist_ok=True)
    sandbox_name = f"{agent_id}_{LLM_MODEL.replace('/','-')}_{timestamp}_{rd}"
    sandbox = run_dir / sandbox_name

    instances_src = (
        Main_Path / f"benchmark/papers/{task_id}/{figure_id}/data"
        if figure_id
        else Main_Path / f"benchmark/papers/{task_id}/data"
    )
    if instances_src.exists() and any(instances_src.iterdir()):
        shutil.copytree(instances_src, sandbox)
    else:
        sandbox.mkdir(parents=True, exist_ok=True)
    shutil.copytree(Main_Path / "utils", sandbox / "utils")

    # Write .env into sandbox
    openai_key = os.environ.get("OPENAI_API_KEY", "")
    with open(sandbox / ".env", "w") as f:
        f.write(f"OPENAI_API_KEY={openai_key}\n")
        f.write(f"ANTHROPIC_API_KEY={os.environ.get('ANTHROPIC_API_KEY', '')}\n")
        f.write(f"GOOGLE_API_KEY={os.environ.get('GOOGLE_API_KEY', '')}\n")
        f.write(f"HF_TOKEN={os.environ.get('HF_TOKEN', '')}\n")

    # Read instruction
    inst_dir = Main_Path / "benchmark" / "papers" / task_id
    if figure_id:
        inst_dir = inst_dir / figure_id
    instruction_file = inst_dir / "instruction" / "instruction.txt"
    with open(instruction_file, "r", encoding="utf-8") as f:
        instruction_text = f.read().strip()

    # Log file
    log_file = (
        Main_Path / "log" / agent_id / LLM_MODEL / task_id
        / f"{timestamp}_{rd}" / "log.log"
    )
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # Prepare execution env
    exec_env = os.environ.copy()
    exec_env["OPENAI_API_KEY"] = openai_key

    # Init OpenAI client
    client = OpenAI(api_key=openai_key)

    # List sandbox contents for the agent
    sandbox_files = []
    for p in sorted(sandbox.rglob("*")):
        if p.is_file() and ".env" not in p.name:
            sandbox_files.append(str(p.relative_to(sandbox)))
    files_listing = "\n".join(sandbox_files[:50]) or "(empty)"

    # Build initial messages
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"## Research Task\n\n{instruction_text}\n\n"
                f"## Working Directory\n"
                f"Your working directory is: {sandbox}\n\n"
                f"## Files Available\n```\n{files_listing}\n```\n\n"
                f"Begin your research. Write Python code to execute experiments."
            ),
        },
    ]

    log_lines = [
        f"agent_id: {agent_id}",
        f"task_id: {task_id}",
        f"llm_model: {LLM_MODEL}",
        "=" * 40,
    ]

    conclusion = None
    for turn in range(MAX_TURNS):
        print(f"  [{task_id}] Turn {turn+1}/{MAX_TURNS} ...")

        # Choose correct token param based on model
        api_kwargs = {
            "model": LLM_MODEL,
            "messages": messages,
        }
        # Most newer models only support temperature=1 and max_completion_tokens
        if any(LLM_MODEL.startswith(p) for p in ["o4", "o3", "o1"]):
            api_kwargs["max_completion_tokens"] = 16384
        elif any(LLM_MODEL.startswith(p) for p in ["gpt-5"]):
            api_kwargs["max_completion_tokens"] = 4096
        else:
            api_kwargs["max_tokens"] = 4096

        try:
            response = client.chat.completions.create(**api_kwargs)
            assistant_msg = response.choices[0].message.content or ""
        except Exception as e:
            assistant_msg = f"API ERROR: {e}"
            log_lines.append(f"\n--- TURN {turn+1} (API ERROR) ---\n{assistant_msg}")
            break

        messages.append({"role": "assistant", "content": assistant_msg})
        log_lines.append(f"\n--- TURN {turn+1} (ASSISTANT) ---\n{assistant_msg}")

        # Check for conclusion
        conclusion = extract_conclusion(assistant_msg)
        if conclusion:
            log_lines.append(f"\n--- FINAL CONCLUSION ---\n{conclusion}")
            break

        # Extract and run code blocks
        code_blocks = extract_code_blocks(assistant_msg)
        if not code_blocks:
            # No code and no conclusion - prompt to continue
            messages.append({
                "role": "user",
                "content": "Please write Python code to run experiments, or provide your FINAL CONCLUSION: if you are done.",
            })
            continue

        all_output = []
        for i, code in enumerate(code_blocks):
            output = run_code(code, sandbox, exec_env)
            all_output.append(f"[Code block {i+1} output]\n{output}")
            log_lines.append(f"\n--- CODE BLOCK {i+1} ---\n{code}\n--- OUTPUT ---\n{output}")

        combined = "\n\n".join(all_output)
        messages.append({"role": "user", "content": f"Execution results:\n\n{combined}"})

    # If no explicit conclusion, ask for one
    if not conclusion:
        messages.append({
            "role": "user",
            "content": "Time is up. Please provide your FINAL CONCLUSION: summarizing all findings.",
        })
        try:
            api_kwargs["messages"] = messages
            response = client.chat.completions.create(**api_kwargs)
            final = response.choices[0].message.content or ""
            conclusion = extract_conclusion(final) or final
            log_lines.append(f"\n--- FORCED FINAL ---\n{final}")
        except Exception as e:
            conclusion = f"Failed to get conclusion: {e}"

    # Write result to log
    log_lines.append(f"\n{'='*40}\nresult: {conclusion}")
    # Also write as JSON for eval compatibility
    log_lines.append(json.dumps({"result": conclusion}))

    with open(log_file, "w", encoding="utf-8") as f:
        f.write("\n".join(log_lines))

    print(f"  [{task_id}] Done. Log: {log_file}")


if __name__ == "__main__":
    main()
