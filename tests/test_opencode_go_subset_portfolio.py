import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.rewrite_instructions import (
    load_portfolio,
    model_block_for_task,
    rewrite_instruction,
    rewrite_instruction_text,
)


def test_opencode_go_subset_portfolio_contains_only_selected_tasks() -> None:
    portfolio = load_portfolio(Path("configs/opencode_go_subset.json"))

    assert set(portfolio) == {
        "questbench",
        "counterfactual_simulatability",
        "cot_in_planning",
        "awareness_detection",
        "llms_assume_rationality",
    }


def test_opencode_go_subset_model_block_uses_three_default_go_models() -> None:
    portfolio = load_portfolio(Path("configs/opencode_go_subset.json"))

    block = model_block_for_task(portfolio, "questbench")

    assert "deepseek-v4-flash" in block
    assert "deepseek-v4-pro" in block
    assert "qwen3.6-plus" in block
    assert "kimi-k2.6" not in block
    assert 'LLMInference(provider="opencode_go", model_name=MODEL_NAME)' in block
    assert "Computational budget: 30 API calls per model" in block


def test_opencode_go_subset_portfolio_is_valid_json() -> None:
    path = Path("configs/opencode_go_subset.json")

    loaded = json.loads(path.read_text(encoding="utf-8"))

    assert isinstance(loaded, dict)


def test_rewrite_instruction_text_replaces_only_model_block() -> None:
    original = """Intro

Models:
- old model
- Computational budget: 1000 API calls per model

Datasets:
- keep this
"""

    rewritten = rewrite_instruction_text(original, "Models:\n- OpenCode Go: deepseek-v4-flash")

    assert (
        rewritten
        == """Intro

Models:
- OpenCode Go: deepseek-v4-flash

Datasets:
- keep this
"""
    )


def test_rewrite_instruction_creates_stable_backup(tmp_path: Path) -> None:
    instruction = tmp_path / "instruction.txt"
    instruction.write_text(
        """Intro

Model:
- old model

Datasets:
- keep this
""",
        encoding="utf-8",
    )

    rewrite_instruction(instruction, "Models:\n- OpenCode Go: deepseek-v4-flash", dry_run=False)
    first_backup = (tmp_path / "instruction.txt.orig.bak").read_text(encoding="utf-8")
    rewrite_instruction(instruction, "Models:\n- OpenCode Go: qwen3.6-plus", dry_run=False)

    assert (tmp_path / "instruction.txt.orig.bak").read_text(encoding="utf-8") == first_backup
    assert "qwen3.6-plus" in instruction.read_text(encoding="utf-8")
