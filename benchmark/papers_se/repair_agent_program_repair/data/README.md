# Data

This directory contains the agent-visible data for the RepairAgent FIRE-Bench-SE pilot task.

The evaluated agent workspace must not include the source paper, `instruction_gt.txt`, `conclusion.txt`, or direct final-result summary files.

Current package:

- `bug_sample.txt`: fixed bounded Defects4J sample for smoke execution.
- `replay_repair_agent_sample.py`: bounded Defects4J replay helper for stored RepairAgent patch candidates.
- `reconstruct_repair_agent_aggregate.py`: helper that reconstructs aggregate Defects4J and baseline counts from released artifact inputs.
- `repair_agent_artifact/`: sanitized RepairAgent artifact subset.
- `repair_agent_artifact/_manifest.json`: copied/skipped file manifest.
- `repair_agent_artifact/repair_agent/Dockerfile`: original container recipe for repository-driven execution.
- `repair_agent_artifact/data/final_list_of_fixed_bugs`: released fixed-bug list used to reconstruct correct-fix counts.
- `repair_agent_artifact/data/fixes_implementation`: released manual-review notes for developer-fix comparison provenance.
- `repair_agent_artifact/repair_agent/experimental_setups/generate_main_table.py` and related setup scripts/lists: released aggregate reconstruction inputs for Defects4J and baseline comparisons.

The visible package is intentionally repository-driven. It contains runnable code, configuration, helper scripts, patch candidates, and released aggregate reconstruction inputs. It does not include the source paper, hidden conclusion, `instruction_gt.txt`, GitBug-Java execution results, ablation execution results, or a prose answer file.

This task declares the `se-java-defects4j` runtime profile in `task_config.yaml`. That profile is an evaluator-side execution prerequisite, not an agent-visible answer source or a task-specific runner wrapper.

Use `replay_repair_agent_sample.py` for bounded smoke reproduction before attempting larger patch replay. The helper checks Defects4J output for `Failing tests: 0`; process return code alone is not treated as a plausible-patch signal. Its default budget replays one stored candidate per sampled bug and can be increased with `--max-candidates-per-bug` when runtime allows.

Use `reconstruct_repair_agent_aggregate.py` to reconstruct full Defects4J aggregate counts from the released artifact inputs. Inspect the helper output and source files before using a number in a final conclusion. Treat bounded replay and aggregate reconstruction as separate evidence streams.

Sanitized artifact contents before adding the aggregate reconstruction inputs:

- 2,982 copied files.
- 6,614 skipped files.
- 826 root patch files.
- 1,963 derivated patch JSON files.

The sanitized artifact keeps direct paper/conclusion leaks out, but it now includes the released aggregate reconstruction inputs needed to reproduce the main Defects4J and baseline counts from the artifact itself. The GitBug-Java sample list is present; the corresponding full execution results are not.

Regenerate the sanitized artifact subset from a manually downloaded and extracted RepairAgent archive:

```bash
uv run --frozen python scripts/prepare_repair_agent_dataset.py \
  --artifact-root /path/to/RepairAgent-reviewed
```
