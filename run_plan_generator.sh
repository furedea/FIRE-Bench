#!/bin/bash
# =====================================================
# Generate instruction_gt.txt for benchmark papers.
#
# Usage:
#   bash run_plan_generator.sh [--papers ...] [--pdf_dir ...] [--model ...] [--tree_dir ...] [--max_tokens ...] [--temperature ...]
#
# --papers      space-separated list of paper folder names OR paths, or a glob
#               pattern for paper directories under benchmark/papers/
#               e.g. "lost_in_the_middle mcq_selection_bias"
#               e.g. "benchmark/papers/*"
#
# --pdf_dir     directory where PDFs live (default: benchmark/pdfs).
#               Each PDF is expected to be named <paper_folder_name>.pdf.
#               Ignored if the PDF is found directly inside the paper folder.
#
# --tree_dir    directory containing pre-computed *_tree.json files (optional)
#
# Examples:
#   bash run_plan_generator.sh --papers "lost_in_the_middle mcq_selection_bias"
#   bash run_plan_generator.sh --papers "benchmark/papers/*" --tree_dir benchmark/trees
#   bash run_plan_generator.sh --papers "benchmark/papers/*" --temperature 1
# =====================================================

# Load environment variables from .env
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

set -e

# ==============================
# Defaults
# ==============================
GENERATOR_SCRIPT="benchmark/plan_generator.py"
DEFAULT_MODEL="gpt-5"
DEFAULT_PDF_DIR="eval/RAGChecker/papers"
DEFAULT_TREE_DIR=""
DEFAULT_MAX_TOKENS=16384
DEFAULT_TEMPERATURE=0.0
PAPERS_ROOT="benchmark/papers"

# ==============================
# Parse CLI arguments
# ==============================
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --papers)      PAPERS="$2"; shift ;;
        --pdf_dir)     PDF_DIR="$2"; shift ;;
        --model)       MODEL="$2"; shift ;;
        --tree_dir)    TREE_DIR="$2"; shift ;;
        --max_tokens)  MAX_TOKENS="$2"; shift ;;
        --temperature) TEMPERATURE="$2"; shift ;;
        *) echo "[!] Unknown parameter: $1"; exit 1 ;;
    esac
    shift
done

MODEL=${MODEL:-$DEFAULT_MODEL}
PDF_DIR=${PDF_DIR:-$DEFAULT_PDF_DIR}
TREE_DIR=${TREE_DIR:-$DEFAULT_TREE_DIR}
MAX_TOKENS=${MAX_TOKENS:-$DEFAULT_MAX_TOKENS}
TEMPERATURE=${TEMPERATURE:-$DEFAULT_TEMPERATURE}

if [ -z "$PAPERS" ]; then
    echo "[!] No papers specified. Use --papers \"paper_name1 paper_name2\" or --papers \"benchmark/papers/*\""
    exit 1
fi

# Resolve each entry: could be a folder name, an absolute path, or a glob
IFS=' ' read -ra RAW_LIST <<< "$PAPERS"
PAPER_DIRS=()
for entry in "${RAW_LIST[@]}"; do
    for expanded in $entry; do
        if [ -d "$expanded" ]; then
            PAPER_DIRS+=("$expanded")
        elif [ -d "${PAPERS_ROOT}/${expanded}" ]; then
            PAPER_DIRS+=("${PAPERS_ROOT}/${expanded}")
        else
            echo "[warn] Could not resolve paper directory: $expanded — skipping."
        fi
    done
done

if [ ${#PAPER_DIRS[@]} -eq 0 ]; then
    echo "[!] No valid paper directories found."
    exit 1
fi

echo "===================================="
echo "Starting instruction_gt Generation"
echo "------------------------------------"
echo "Papers:      ${#PAPER_DIRS[@]} directory/ies"
echo "Model:       $MODEL"
echo "PDF dir:     $PDF_DIR"
echo "Tree dir:    ${TREE_DIR:-<none>}"
echo "Max tokens:  $MAX_TOKENS"
echo "Temperature: $TEMPERATURE"
echo "===================================="
echo

TOTAL=${#PAPER_DIRS[@]}
SUCCESS=0
FAILED=0

for paper_dir in "${PAPER_DIRS[@]}"; do
    BASENAME=$(basename "$paper_dir")

    # Resolve PDF: prefer one inside the paper folder, else look in PDF_DIR
    PDF_ARG=""
    PDF_IN_DIR=$(ls "${paper_dir}"/*.pdf 2>/dev/null | head -1)
    if [ -n "$PDF_IN_DIR" ]; then
        PDF_ARG="--pdf $PDF_IN_DIR"
    elif [ -f "${PDF_DIR}/${BASENAME}.pdf" ]; then
        PDF_ARG="--pdf ${PDF_DIR}/${BASENAME}.pdf"
    else
        echo "[warn] No PDF found for $BASENAME (checked ${paper_dir}/ and ${PDF_DIR}/${BASENAME}.pdf)"
        FAILED=$((FAILED + 1))
        continue
    fi

    # Resolve optional tree JSON
    TREE_ARG=""
    if [ -n "$TREE_DIR" ] && [ -f "${TREE_DIR}/${BASENAME}_tree.json" ]; then
        TREE_ARG="--tree ${TREE_DIR}/${BASENAME}_tree.json"
    fi

    echo "===================================================="
    echo "Paper dir: $paper_dir"
    echo "===================================================="

    if python "$GENERATOR_SCRIPT" "$paper_dir" \
        $PDF_ARG \
        --model "$MODEL" \
        --max-tokens "$MAX_TOKENS" \
        --temperature "$TEMPERATURE" \
        $TREE_ARG; then
        SUCCESS=$((SUCCESS + 1))
    else
        echo "[!] Failed for: $paper_dir"
        FAILED=$((FAILED + 1))
    fi

    echo
done

echo "===================================="
echo "instruction_gt generation completed"
echo "------------------------------------"
echo "Total:   $TOTAL"
echo "Success: $SUCCESS"
echo "Failed:  $FAILED"
echo "===================================="
