# FIRE-Bench-SE Candidate Shortlist

This file records the first-pass shortlist for a FIRE-Bench-style software engineering benchmark. The list is intentionally conservative: entries are candidate tasks, not accepted tasks. Each candidate still needs artifact inspection and problem-tree construction before it can become a benchmark task.

## Source Corpus

The first pass inspected public research-track pages for ICSE 2025, FSE 2025, ASE 2025, ICSE 2026, and FSE 2026. FSE 2026 has an accepted-paper list, but candidate triage is deferred until artifacts are stable. ASE 2026 is deferred until research-paper decisions and artifacts are public.

Primary sources checked:

- [FIRE-Bench paper](https://firebench.github.io/static/FIRE_Bench.pdf) for the original constrained-rediscovery and source-paper filtering protocol.
- [ICSE 2025 Research Track](https://conf.researchr.org/track/icse-2025/icse-2025-research-track).
- [ICSE 2026 Research Track](https://conf.researchr.org/track/icse-2026/icse-2026-research-track).
- [FSE 2025 Research Papers](https://conf.researchr.org/track/fse-2025/fse-2025-research-papers).
- [FSE 2026 Research Papers](https://conf.researchr.org/track/fse-2026/fse-2026-research-papers).
- [ASE 2025 Research Papers](https://conf.researchr.org/track/ase-2025/ase-2025-papers).
- [ASE 2026 Research Papers](https://conf.researchr.org/track/ase-2026/ase-2026-research-track).
- [MSR 2025 Technical Papers](https://2025.msrconf.org/track/msr-2025-technical-papers).

## High-Priority Candidates

| Candidate ID | Venue | Year | Paper | Topic | Why It Fits | Initial Risk |
| --- | --- | --: | --- | --- | --- | --- |
| `repair_agent_program_repair` | ICSE | 2025 | RepairAgent: An Autonomous, LLM-Based Agent for Program Repair | APR / LLM agents | Uses Defects4J and reports concrete repair counts, including bugs not fixed by prior techniques. | API/model drift may affect rediscovery. |
| `rug_rust_unit_tests` | ICSE | 2025 | RUG: Turbo LLM for Rust Unit Test Generation | Test generation | Reports coverage and accepted generated tests on real Rust projects. | Needs artifact and project version inspection. |
| `deprecated_api_completion` | ICSE | 2025 | LLMs Meet Library Evolution: Evaluating Deprecated API Usage in LLM-based Code Completion | Maintenance / code completion | Large controlled evaluation with 145 API mappings, eight Python libraries, and 28,125 prompts. | API and model availability may need a smaller frozen subset. |
| `human_evo_repo_generation` | ICSE | 2025 | HumanEvo: An Evolution-aware Benchmark for More Realistic Evaluation of Repository-level Code Generation | Repository-level code generation | Introduces a benchmark and execution-based evaluation for repository evolution. | Dataset availability must be confirmed. |
| `llm_assisted_wasm_testing` | ICSE | 2025 | LWDIFF: An LLM-Assisted Differential Testing Framework for WebAssembly Runtimes | Differential testing | Reports branch coverage and confirmed bugs across eight Wasm runtimes. | Runtime setup may be heavy. |
| `repo_security_patch_detection` | ICSE | 2025 | Repository-Level Graph Representation Learning for Enhanced Security Patch Detection | Security patch detection | Uses named datasets and reports quantitative improvements over baselines. | Model training may be too heavy; may need an analysis-only task. |
| `vulnerability_patch_porting` | FSE | 2025 | Mystique: Automated Vulnerability Patch Porting with Semantic and Syntactic-Enhanced LLM | Vulnerability patching | Research-track security task with clear SE relevance. | Artifact and benchmark details need inspection. |
| `vulnerability_fix_detection_by_llm` | FSE | 2025 | Code Change Intention, Development Artifact and History Vulnerability: Putting Them Together for Vulnerability Fix Detection by LLM | Vulnerability fix detection | Combines code, artifacts, and history; likely suitable for claim-level rediscovery. | Need public data and metrics. |
| `performance_bugs_data_science` | FSE | 2025 | Towards Understanding Performance Bugs in Popular Data Science Libraries | Performance bugs | Empirical characterization task likely suitable for repository-mining rediscovery. | Data extraction may be more curation-heavy. |
| `security_debt_llm_agents` | ASE | 2025 | Security Debt in LLM Agent Applications: A Measurement Study of Vulnerabilities and Mitigation Trade-offs | Security / LLM agent applications | Measurement-study shape matches FIRE-Bench well. | Artifact and dataset release must be confirmed. |
| `altered_histories_vcs` | ASE | 2025 | Altered Histories in Version Control System Repositories: Evidence from the Trenches | Repository mining | Empirical evidence over version-control histories; likely rich in verifiable claims. | May require large-scale mining. |
| `promfuzz_smart_contracts` | ASE | 2025 | PROMFUZZ: Leveraging LLM-Driven and Bug-Oriented Composite Analysis for Detecting Functional Bugs in Smart Contracts | Fuzzing / smart contracts | Concrete bug-finding evaluation with a security/testing angle. | Blockchain toolchain may be brittle. |
| `rust_issue_resolution_agents` | ICSE | 2026 | Evaluating and Improving Automated Repository-Level Rust Issue Resolution with LLM-based Agents | Issue resolution / agents | Directly aligned with agent-based SE and likely benchmark-driven. | 2026 artifact stability unknown. |
| `coding_agent_turn_control` | ICSE | 2026 | More with Less: An Empirical Study of Turn-Control Strategies for Efficient Coding Agents | Coding agents | Empirical study of agent strategy; likely compute-light with clear treatment variables. | Exact artifact availability unknown. |
| `agent_ensemble_issue_resolution` | ICSE | 2026 | Agent-Based Ensemble Reasoning for Repository-Level Issue Resolution | Issue resolution / agents | Repository-level issue resolution with a preprint link. | 2026 and agent-stack dependencies may be unstable. |

## Initial Artifact Triage

| Candidate ID | Artifact status | Task-construction status |
| --- | --- | --- |
| `repair_agent_program_repair` | Public GitHub repository found: <https://github.com/sola-st/RepairAgent>. Archived Zenodo artifact found: <https://zenodo.org/records/14872682> (`10.5281/zenodo.14872682`). The README documents Defects4J batches, analysis scripts, fixed-bug lists, patch data, and table-generation scripts. | First pilot task skeleton created under `benchmark/papers_se/repair_agent_program_repair/`. Next step is a sanitized data subset and a dry agent pass. |
| `rug_rust_unit_tests` | Official ICSE page links a preprint and "RUG Repo"; repository details still need inspection. | Promising, but task construction should wait until the repo and Rust project versions are frozen. |
| `deprecated_api_completion` | arXiv/preprint found; artifact still needs confirmation. | Promising because prompts and API mappings are naturally tabular, but public data must be verified before inclusion. |
| `vulnerability_fix_detection_by_llm` | arXiv/preprint found; artifact and BigVulFixes availability still need confirmation. | Keep as reserve until the dataset can be inspected. |
| `security_debt_llm_agents` | Preprint found; artifact/data release still needs confirmation. | Good measurement-study shape, but do not accept until the app corpus and annotations are public. |

## Pilot Recommendation

Start with five candidates that cover different SE subareas and minimize setup risk:

1. `repair_agent_program_repair`
2. `deprecated_api_completion`
3. `rug_rust_unit_tests`
4. `vulnerability_fix_detection_by_llm`
5. `security_debt_llm_agents`

Keep `rust_issue_resolution_agents` and `coding_agent_turn_control` as 2026 reserve tasks after artifacts stabilize.

If only one task is built first, start with `repair_agent_program_repair` because it already has a public repository, explicit replication commands, and a clear published finding: 164 Defects4J bugs fixed, including 39 not fixed by prior techniques.

## Next Checks

For each pilot candidate:

1. Locate the official paper PDF or author preprint.
2. Locate artifact, replication package, or dataset release.
3. Verify license and whether redistribution under `benchmark/papers_se` is allowed.
4. Extract the main research-problem tree.
5. Select one target leaf with a figure, table, or named result section.
6. Draft `instruction.txt`, `instruction_gt.txt`, `conclusion.txt`, and `dataset.txt`.
7. Run one dry agent pass in an isolated workspace to check leakage and executability.
