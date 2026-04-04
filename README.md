<h3 align="center">
  <strong>🔥 FIRE-Bench: Evaluating Agents on the Rediscovery of Scientific Insights</strong>
</h3>

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

### 1. Download Data for Specific Benchmark

In `benchmark` folder, some papers have empty `data` folder since the data can be loaded directly from HuggingFace. The sources of the data in nonempty data folder are described in `dataset.txt`.

### 2. Parse Other Papers into Problem Trees (Optional)

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

### 3. Benchmark Your Own Agent

You can use FIRE-Bench to evaluate any agent system beyond the built-in ones (Codex, Claude Code, OpenHands).

#### Benchmark Task Structure

Each task in `benchmark/papers/<task_id>/` contains:

```
benchmark/papers/<task_id>/
├── instruction/
│   ├── instruction.txt       # Research prompt for the agent
│   └── instruction_gt.txt    # (some tasks) Ground-truth experimental plan
└── data/                     # (optional) Datasets for the task
```

- **`instruction.txt`** defines the research question, available resources (models, datasets), and constraints.
- **`data/`** contains task-specific datasets. Some tasks load data directly from HuggingFace instead (described in the instruction).

There are 35 benchmark tasks spanning topics such as CoT reasoning, hallucination, bias, safety, multimodal understanding, and more.

#### Step A: Prepare the Agent's Working Directory

For each task you want to evaluate, set up a working directory for your agent:

1. Copy `benchmark/papers/<task_id>/data/` (if it exists) into the working directory as `data/`
2. Copy the project-level `utils/` folder into the working directory (provides `LLMInference` and other shared helpers)
3. Create a `.env` file with API keys so the agent can call LLMs during experiments

#### Step B: Run Your Agent

Read the prompt from `benchmark/papers/<task_id>/instruction/instruction.txt` and pass it to your agent as the task instruction. The agent should:

- Design and execute experiments using the provided datasets and models
- Produce a final conclusion summarizing its findings

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

The pipeline decomposes both the agent's conclusion and the ground-truth into atomic claims, then computes **Precision**, **Recall**, and **F₁** via claim-level analysis.

### 4. Run Built-in Experiments

Edit `run_experiment.sh` to configure your agent/task/model combinations, then run:

```bash
bash run_experiment.sh
```

This iterates over all combinations of `AGENT_IDS`, `TASK_IDS`, and `LLM_MODELS`, calling `run_agent.py` for each. Results are saved to the `log/` folder.

**Parameters in `run_experiment.sh`:**
- `AGENT_IDS`: agents to run (e.g., `codex`, `claude_code`, `openhands`)
- `TASK_IDS`: benchmark tasks (e.g., `rational`)
- `LLM_MODELS`: models to use (e.g., `gpt-5`)

### 5. Evaluate Results

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

