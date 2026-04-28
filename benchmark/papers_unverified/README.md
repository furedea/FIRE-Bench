# Unverified benchmark tasks

These tasks were generated automatically by Paper2Bench from the paper list in
`c:/Work/FIRE-Bench/unverified_papers.json`.

**Status: UNVERIFIED.** Unlike the human-curated tasks under `../papers/`, these
have not been hand-checked. Known caveats:

- The arxiv search may have downloaded a different paper than the one named in
  the JSON entry (similarity-rerank rejects mismatches but doesn't catch every
  case).
- Research questions, dataset lists, and ground-truth plans are LLM-extracted
  from the PDF — content accuracy depends on the extraction prompt.
- Roughly 25% of dataset entries are still `source: unknown` (no HF Hub match
  and no public URL the locator could validate); the rest have one of:
  - `source: huggingface` with a verified `load_dataset(...)` call
  - `source: external` with a HEAD-validated URL (GitHub repo / project page)
  - `source: synthetic` with generation code

Each task directory mirrors the layout of `../papers/<task_id>/`:

    instruction/
      instruction.txt        -- what the agent sees
      instruction_gt.txt     -- ground-truth plan (for evaluation)

The original `task_config.yaml` (from which `instruction.txt` was rendered)
lives next to the `instruction/` folder for provenance.

To promote a task to verified, copy it under `../papers/` after manual review.
