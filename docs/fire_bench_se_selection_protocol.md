# FIRE-Bench-SE Selection Protocol

## Goal

Build a FIRE-Bench-style pilot for software engineering research by selecting empirical, artifact-backed findings from top SE venues in 2025-2026. The pilot goal is five executable constrained-rediscovery tasks; the expansion goal is a 30-task benchmark mirroring the scale of FIRE-Bench.

## Scope

FIRE-Bench-SE adapts the FIRE-Bench constrained-rediscovery setup to software engineering research. The benchmark should evaluate whether an agent can rediscover established empirical findings from top software engineering venues, not whether it can directly reproduce a paper after reading the full paper.

The initial corpus is restricted to research-track full papers from:

- ICSE 2025-2026
- FSE 2025-2026
- ASE 2025-2026

ISSTA and MSR can be added as focused extensions for testing, analysis, and mining-software-repositories tasks. Papers are included only if they are public by the corpus freeze date.

Use a corpus freeze date before producing a benchmark release. For the initial pilot, freeze at the date of collection and mark 2026 papers as provisional unless their accepted-paper page, PDF, and artifacts are already public.

## FIRE-Bench Alignment

FIRE-Bench builds tasks from recent, high-impact empirical analysis papers. Each paper is decomposed into a research-problem tree. A target leaf corresponds to a central experimental finding, while the agent receives an intermediate research question that preserves exploration freedom. The original method and conclusion are withheld, and evaluation compares the agent conclusion against the published finding using claim-level precision, recall, and F1.

The source FIRE-Bench paper uses the following selection logic:

- Source pool: empirical analysis papers on LLM behavior from ICLR, ICML, and NeurIPS in 2024-2025, using top-tier venues as a research-impact proxy.
- Filtering: keyword search over proceedings, LLM-based classification for empirical analysis of LLM behavior, then two-author manual review.
- Retention criteria: open inputs, compute-light execution, and non-trivial verifiable insights supported by explicit figures or tables.
- Task instantiation: select a central target leaf tied to a main figure or table, then give the agent the parent intermediate research question plus inherited scope and evaluation criteria.

FIRE-Bench-SE keeps the same task abstraction:

- one task per selected paper;
- one target leaf per task;
- agent input from an intermediate research-question node;
- hidden ground-truth conclusion from the target experimental leaf;
- claim-level evaluation against the hidden conclusion.

## Inclusion Criteria

Candidate papers must satisfy all core criteria.

1. The paper is a research-track full paper from an in-scope venue and year.
2. The paper reports empirical results tied to concrete figures, tables, or named result sections.
3. The paper has open inputs: data, repositories, benchmarks, tools, prompts, test suites, or a replication package sufficient for an agent to run a lightweight rediscovery experiment.
4. The main finding is non-trivial and claim-verifiable.
5. The task can be run with modest compute: no large model training, no private infrastructure, and no unavailable proprietary datasets.
6. The agent can investigate the question from the released inputs without seeing the original paper, the detailed method, or the target conclusion.

The SE-specific interpretation of the FIRE-Bench retention criteria is:

| FIRE-Bench criterion | FIRE-Bench-SE interpretation |
| --- | --- |
| Open inputs | Public repositories, benchmark instances, test suites, issue/PR data, prompts, or replication packages are sufficient for a lightweight rediscovery run. |
| Compute-light execution | No large training job, private infrastructure, or full-scale repository crawl is required for the core finding. A bounded subset must be runnable locally or with a practical API budget. |
| Non-trivial, verifiable insights | The paper reports directional, comparative, or quantitative claims tied to a figure, table, or named result section. |

## Exclusion Criteria

Exclude papers when any condition applies.

- The contribution is primarily theoretical or design-only.
- The paper proposes a method but lacks an empirical insight suitable for rediscovery.
- The critical data is private, industrial-only, or ethically unavailable.
- The result depends on human-subject raw data that is not released.
- The experiment requires large-scale model training or expensive infrastructure.
- The expected answer would be a paper-reading summary rather than an empirical conclusion supported by agent-run analysis.

## Screening Rubric

Each candidate receives a 10-point screening score.

| Axis | Points | Question |
| --- | --: | --- |
| Open inputs | 0-2 | Are the data, benchmark, code, or artifacts public and usable? |
| Compute-light execution | 0-2 | Can the rediscovery task run within a practical local or API budget? |
| Verifiable insight | 0-2 | Can the conclusion be decomposed into atomic claims? |
| Balanced openness | 0-2 | Is the intermediate RQ neither too broad nor too prescriptive? |
| SE centrality | 0-1 | Is the topic central to software engineering? |
| Operational reliability | 0-1 | Are versions, commits, tests, and metrics clear enough to automate? |

Use 7/10 as the threshold for pilot inclusion. Keep 5-6/10 papers in a reserve pool when they look promising but require artifact inspection.

## Collection Workflow

1. Collect research-track accepted papers from official conference pages.
2. Normalize metadata: venue, year, track, title, authors, DOI, preprint, artifact URL, dataset URL, and topic.
3. Apply keyword filtering for SE subareas: repair, testing, fuzzing, program analysis, repository mining, maintenance, issue resolution, vulnerability, security, LLM4SE, and developer behavior.
4. Apply manual screening with the rubric above.
5. For candidates scoring at least 7/10, inspect artifacts before task construction.
6. Build a problem tree from the paper PDF, choose one central target leaf, and draft the hidden and visible task files.

## Task Construction

For each selected paper, create:

```text
benchmark/papers_se/<task_id>/
  instruction/instruction.txt
  instruction/instruction_gt.txt
  conclusion.txt
  dataset.txt
  task_config.yaml
  data/
```

`instruction.txt` contains the high-level research question, available resources, models or tools, datasets, metrics, budget, and constraints. It must not reveal the original method, exact result numbers, or target conclusion.

`instruction_gt.txt` records the hidden procedural plan used for auditing and debugging. It should map steps back to the target paper's figures, tables, or result sections.

`conclusion.txt` contains short, human-authored ground-truth claims from the target leaf. Claims should be specific enough to judge precision and recall.

`dataset.txt` records upstream artifact locations, licenses, frozen versions, download dates, and any preprocessing.

## Pilot Target

The pilot should contain five tasks:

1. LLM or agent-based software engineering.
2. Automated program repair or bug fixing.
3. Software testing or test generation.
4. Vulnerability or security analysis.
5. Repository mining, maintenance, or developer-behavior analysis.

Prefer ICSE/FSE/ASE 2025 first because proceedings and artifacts are more likely to be stable. Add 2026 papers only after the freeze date confirms public access.
