import subprocess
import os
import sys
import time
import random
from pathlib import Path
import shutil
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Repo path
Main_Path = Path.cwd()

def main():
    # Prepare environment variables
    agent_id = os.environ.get("AGENT_ID", "")
    task_id = os.environ.get("TASK_ID", "")
    figure_id = os.environ.get("FIGURE_ID", "")
    LLM_MODEL = os.environ.get("LLM_MODEL", "")

    # Timestamp for run naming
    timestamp = time.strftime("%Y%m%d%H%M%S")
    run_name = f"codex-run-{timestamp}"

    # A random suffix
    rd = random.randint(10000, 99999)

    # Ensure run/ directory exists
    run_dir = Main_Path / "runs"
    run_dir.mkdir(parents=True, exist_ok=True)

    # Build the sandbox directory
    sandbox_volume_filename = f"{agent_id}_{LLM_MODEL.replace('/','-')}_{timestamp}_{rd}"
    sandbox_volume_path = run_dir / sandbox_volume_filename

    # Copy experiment setup
    instances_src = Main_Path / f"benchmark/papers/{task_id}/{figure_id}/data" if figure_id else Main_Path / f"benchmark/papers/{task_id}/data"
    if instances_src.exists():
        shutil.copytree(instances_src, sandbox_volume_path)
    else:
        # Some tasks generate data programmatically; create empty sandbox
        sandbox_volume_path.mkdir(parents=True, exist_ok=True)
    utils_src = Main_Path / "utils"
    shutil.copytree(utils_src, sandbox_volume_path / "utils")

    # Instruction path
    INSTRUCTION_PATH = Main_Path / "benchmark" / "papers" / task_id / (figure_id if figure_id else "") / "instruction"
    instruction_file = INSTRUCTION_PATH / "instruction.txt"

    # Log file
    log_file = Main_Path / "log" / f"{agent_id}" / f"{LLM_MODEL}" / f"{task_id}" / f"{timestamp}_{rd}" / "log.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # Write metadata to log
    with open(log_file, "w", encoding="utf-8") as f:
        f.write(f"agent_id: {agent_id}\n")
        f.write(f"task_id: {task_id}\n")
        f.write(f"llm_model: {LLM_MODEL}\n")
        f.write("=" * 40 + "\n")

    with open(instruction_file, "r", encoding="utf-8") as f:
        instruction_text = f.read().strip()

    # Load API keys and settings from .env
    use_subscription = os.environ.get("USE_SUBSCRIPTION", "0") == "1"
    openai_key = os.environ.get("OPENAI_API_KEY", "")
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")
    google_key = os.environ.get("GOOGLE_API_KEY", "")
    hf_token = os.environ.get("HF_TOKEN", "")

    # Write .env into sandbox so utils/llm_inference.py can load API keys
    with open(sandbox_volume_path / ".env", "w") as f:
        f.write(f"OPENAI_API_KEY={openai_key}\n")
        f.write(f"ANTHROPIC_API_KEY={anthropic_key}\n")
        f.write(f"GOOGLE_API_KEY={google_key}\n")
        f.write(f"HF_TOKEN={hf_token}\n")

    # Resolve npx path: on Windows use npx.cmd
    npx_cmd = "npx"
    node_path = Path(r"C:\Program Files\nodejs")
    if node_path.exists():
        npx_candidate = node_path / "npx.cmd"
        if npx_candidate.exists():
            npx_cmd = str(npx_candidate)

    # Build Codex CLI command
    cmd = [
        npx_cmd, "@openai/codex@0.39.0",
        "--model", LLM_MODEL,
        "--config", "sandbox_mode=danger-full-access",
        "exec",
        instruction_text   # <- pass actual prompt string
    ]

    env = os.environ.copy()
    # Ensure Node.js is in PATH
    if node_path.exists():
        env["PATH"] = str(node_path) + os.pathsep + env.get("PATH", "")
    if use_subscription:
        print("Subscription is only available for Claude Code right now, still need OPENAI_API_KEY.")
    else:
        print(f"Running Codex with API key authentication")

    # Run the Codex command and log output
    with open(log_file, "a", encoding="utf-8") as f:
        process = subprocess.run(cmd, cwd=sandbox_volume_path, env=env, stdout=f, stderr=subprocess.STDOUT)

    print(f"Run complete. Logs saved to {log_file}")

if __name__ == "__main__":
    main()
