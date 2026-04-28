<h1 align="center">
  <strong>🔥 FIRE-Bench: Evaluating Agents on the Rediscovery of Scientific Insights</strong>
</h1>

<p align="center">
  <a href="https://arxiv.org/abs/2602.02905">
    <img src="https://img.shields.io/badge/arXiv-2602.02905-red?style=flat-square&logo=arxiv" alt="arXiv">
  </a>
  &nbsp;
  <a href="https://github.com/maitrix-org/FIRE-Bench">
    <img src="https://img.shields.io/badge/GitHub-Project-181717?style=flat-square&logo=github" alt="GitHub">
  </a>
  &nbsp;
  <a href="https://firebench.github.io/">
    <img src="https://img.shields.io/badge/🔥-Website-orange?style=flat-square" alt="Website">
  </a>
</p>


FIRE-Bench is constructed through **research-problem decomposition**, a process that transforms high-quality empirical analysis papers into **verifiable benchmark tasks**. This approach balances:

- **Exploratory freedom** (avoiding tasks that are too broad to benchmark), and  
- **Empirical verifiability** (avoiding tasks that are too narrow to allow genuine exploration).

We evaluate agent performance through **claim-level analysis**. Both agent conclusions **C_agent** and ground-truth conclusions **C_gt** are decomposed into **atomic, verifiable claims**. Overall performance is measured using **Precision**, **Recall**, and the **F_1** score.


## Workflow and Results
<table>
  <tr>
    <td style="width:50%; text-align:center; vertical-align:top;">
      <img src="resources/workflow.png" width="100%" />
    </td>
    <td style="width:50%; vertical-align:top;">

<table>
  <thead>
    <tr>
      <th>#</th>
      <th>Agent</th>
      <th>Prec.</th>
      <th>Recall</th>
      <th>F<sub>1</sub> Score</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>1</td>
      <td>CC<sub>Sonnet-4</sub></td>
      <td><b>52.1</b><sub>±26.1</sub></td>
      <td>48.3<sub>±24.8</sub></td>
      <td><b>46.7</b><sub>±23.4</sub></td>
    </tr>
    <tr>
      <td>2</td>
      <td>CX<sub>gpt-5-med</sub></td>
      <td>44.8<sub>±24.1</sub></td>
      <td><b>49.0</b><sub>±28.5</sub></td>
      <td>41.9<sub>±25.4</sub></td>
    </tr>
    <tr>
      <td>3</td>
      <td>OH<sub>gpt-5</sub></td>
      <td>41.7<sub>±22.7</sub></td>
      <td>41.4<sub>±24.9</sub></td>
      <td>37.9<sub>±23.0</sub></td>
    </tr>
    <tr>
      <td>4</td>
      <td>OH<sub>o4-mini</sub></td>
      <td>36.8<sub>±18.5</sub></td>
      <td>36.6<sub>±19.2</sub></td>
      <td>31.9<sub>±17.6</sub></td>
    </tr>
  </tbody>
</table>

  </td>
  </tr>
</table>



## Setup

### Environment

```bash
mamba create -n firebench python=3.11  # or conda
mamba activate firebench
pip install -r requirements.txt
```

### API Keys

Create a `.env` file:

```
OPENAI_API_KEY=
GOOGLE_API_KEY=
HF_TOKEN=
ANTHROPIC_API_KEY=
USE_SUBSCRIPTION=1 (mark this as 1 if you want to use Claude Code subscription, 0 if using API key; note that some benchmark papers running on Claude models still require ANTHROPIC_API_KEY)
```

### Agent Dependencies

- **Codex**: `npx @openai/codex@0.39.0 --version` (v0.39.0 required for timestamp logging)
- **Claude Code**: [Setup guide](https://code.claude.com/docs/en/setup) or `curl -fsSL https://claude.ai/install.sh | bash`
- **OpenHands**: `export OPENHANDS_HOME=./.openhands; mkdir  -p ./.openhands` (Requires docker)

## Usage

### 1. Benchmark Your Own Agent

You can use FIRE-Bench to evaluate any agent system beyond the built-in ones (Codex, Claude Code, OpenHands). Tasks are published as two HuggingFace datasets — pick whichever fits your evaluation goals:

| Dataset | Tasks | Status |
|---|---|---|
| [`silence-suzuki/FIRE-Bench-verified`](https://huggingface.co/datasets/silence-suzuki/FIRE-Bench-verified) | 35 | Hand-curated by the FIRE-Bench team. Many tasks bundle local data files. |
| [`silence-suzuki/FIRE-Bench-unverified`](https://huggingface.co/datasets/silence-suzuki/FIRE-Bench-unverified) | 153 | Auto-generated end-to-end by the [Paper2Bench](https://github.com/AbhayAnandUCSD/Paper2Bench) pipeline. No human review. |

#### End-to-end skeleton

```python
from datasets import load_dataset
from huggingface_hub import snapshot_download
import os, time

ds = load_dataset("silence-suzuki/FIRE-Bench-verified", split="train")
local = snapshot_download(
    "silence-suzuki/FIRE-Bench-verified", repo_type="dataset",
)  # one-time pull of all data assets

for task in ds:
    tid = task["task_id"]
    work_dir = f"runs/{tid}"
    os.makedirs(work_dir, exist_ok=True)

    # Symlink (or copy) the task's data dir into the agent's CWD if present
    src_data = os.path.join(local, "tasks", tid, "data")
    if os.path.isdir(src_data):
        os.symlink(src_data, os.path.join(work_dir, "data"))

    output = my_agent.run(task["instruction"], cwd=work_dir)

    # Write the log in the expected format
    log_dir = f"log/my_agent/gpt-4o/{tid}/{time.strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(log_dir, exist_ok=True)
    with open(f"{log_dir}/log.log", "w", encoding="utf-8") as f:
        f.write(f"agent_id: my_agent\ntask_id: {tid}\nllm_model: gpt-4o\n")
        f.write("=" * 40 + "\n")
        f.write(output["trajectory"])
        f.write(f'\n{{"result": "{output["final_conclusion"]}"}}\n')
```

#### Schema

Both datasets share the same row shape:

| Field | Description |
|---|---|
| `task_id` | unique identifier (e.g. `reversal_curse_rq0`) |
| `research_question` | the question the agent must answer |
| `instruction` | the full prompt the agent sees (research question + resources + constraints) |
| `instruction_gt` | ground-truth procedural plan (used by the evaluator, **not** shown to the agent) |
| `conclusion` | ground-truth answer; what the agent's final write-up is compared against |

The verified dataset adds `dataset_source` and `has_local_data`; the unverified dataset adds `paper_type` and `task_config` (typed datasets/models/constraints).

#### Step A: Load the Tasks

```python
from datasets import load_dataset

ds = load_dataset("silence-suzuki/FIRE-Bench-verified", split="train")
# or: load_dataset("silence-suzuki/FIRE-Bench-unverified", split="train")

print(f"{len(ds)} tasks")
print(ds[0]["task_id"], "->", ds[0]["research_question"][:80])
```

For tasks where `has_local_data` is true, fetch the bundled files (JSONL, JSON, images, etc.) with `snapshot_download`:

```python
from huggingface_hub import snapshot_download

local_dir = snapshot_download(
    "silence-suzuki/FIRE-Bench-verified",
    repo_type="dataset",
    allow_patterns=["tasks/lost_in_the_middle/**"],
)
# files now live at <local_dir>/tasks/lost_in_the_middle/data/...
```

`tasks/<task_id>/dataset.txt` (when present) documents the upstream source if the curators left a pointer rather than bundling files.

#### Step B: Run Your Agent

Pass `task["instruction"]` to your agent verbatim. The agent should:

- Design and execute experiments using the resources listed in the instruction
- Produce a final written conclusion summarizing its findings

Do **not** show the agent `instruction_gt` or `conclusion` — both are evaluation-only.

#### Step C: Save Output in the Expected Log Format

The evaluation pipeline reads logs from:

```
log/<agent_name>/<model_name>/<task_id>/<timestamp>/log.log
```

Each `log.log` must begin with three metadata lines followed by the full agent output:

```
agent_id: <your_agent_name>
task_id: <task_id>
llm_model: <model_name>
========================================
<full agent trajectory and output>
```

The evaluator extracts the agent's final conclusion from the log. It recognizes three formats — append **one** of these at the end of your log:

| Format | How to emit |
|---|---|
| **JSON (simplest)** | Append a JSON line: `{"result": "<final conclusion>"}` |
| **OpenHands-style** | Include `final_thought='<conclusion>', outputs=` in the log |
| **Codex-style** | Bracket conclusions between `[YYYY-MM-DDTHH:MM:SS]` timestamp lines |

#### Step D: Evaluate

Run the evaluation pipeline on your logs:

```bash
bash run_eval.sh --agents <your_agent_name> --models <model_name> --tasks <task_id>

# Or evaluate everything at once
bash run_eval.sh --agents all --models all --tasks all
```

The pipeline decomposes both the agent's conclusion and the dataset's `conclusion` field into atomic claims, then computes **Precision**, **Recall**, and **F₁** via claim-level analysis.

### 2. Parse Other Papers into Problem Trees

Use the tree parser to decompose a research paper (PDF) into a hierarchical research-problem tree via OpenAI:

```bash
# Single paper
bash run_tree_parser.sh --papers /path/to/paper.pdf

# Multiple papers (quote the list)
bash run_tree_parser.sh --papers "/path/to/paper1.pdf /path/to/paper2.pdf" --model gpt-4o

# Glob pattern for a whole directory
bash run_tree_parser.sh --papers "/path/to/papers/*.pdf" --output_dir benchmark/trees
```

**Options:**
- `--papers`: space-separated PDF paths or a glob pattern (**required**)
- `--model`: OpenAI model name (default: `gpt-4o`)
- `--output_dir`: directory for output JSON trees (default: `benchmark/trees`)
- `--max_tokens`: max output tokens (default: `16384`)
- `--temperature`: sampling temperature (default: `0.0`)

Each paper produces a `<name>_tree.json` file containing the problem tree.

### 3. Run Built-in Experiments

Edit `run_experiment.sh` to configure your agent/task/model combinations, then run:

```bash
bash run_experiment.sh
```

This iterates over all combinations of `AGENT_IDS`, `TASK_IDS`, and `LLM_MODELS`, calling `run_agent.py` for each. Results are saved to the `log/` folder.

**Parameters in `run_experiment.sh`:**
- `AGENT_IDS`: agents to run (e.g., `codex`, `claude_code`, `openhands`)
- `TASK_IDS`: benchmark tasks (e.g., `rational`)
- `LLM_MODELS`: models to use (e.g., `gpt-5`)

### 4. Evaluate Results

After experiments finish, evaluate the generated logs:

```bash
# Evaluate all agents/models/tasks
bash run_eval.sh --agents all --models all --tasks all

# Evaluate a specific run
bash run_eval.sh --agents codex --models gpt-5 --tasks rational --timestamp 20251016232701_10997
```

**Options:**
- `--agents`: agent name or `all`
- `--models`: model name or `all`
- `--tasks`: task name or `all`
- `--timestamp`: (optional) evaluate a specific run by timestamp

