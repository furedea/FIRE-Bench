#!/bin/bash
# =====================================================
# Run tree-parser script
# Usage:
#   bash run_tree_parser.sh [--papers ...] [--model ...] [--output_dir ...] [--max_tokens ...] [--temperature ...]
# Example:
#   bash run_tree_parser.sh --papers /path/to/paper.pdf
#   bash run_tree_parser.sh --papers "/path/to/paper1.pdf /path/to/paper2.pdf" --model gpt-4o
#   bash run_tree_parser.sh --papers "/path/to/*.pdf" --model gpt-4o --output_dir results/trees
# =====================================================

# Load environment variables from .env
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

# Exit immediately on error
set -e

# ==============================
# Default arguments
# ==============================
PARSER_SCRIPT="benchmark/tree_parser.py"
DEFAULT_MODEL="gpt-4o"
DEFAULT_OUTPUT_DIR="benchmark/trees"
DEFAULT_MAX_TOKENS=16384
DEFAULT_TEMPERATURE=0.0

# ==============================
# Parse CLI arguments (optional overrides)
# ==============================
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --papers)      PAPERS="$2"; shift ;;
        --model)       MODEL="$2"; shift ;;
        --output_dir)  OUTPUT_DIR="$2"; shift ;;
        --max_tokens)  MAX_TOKENS="$2"; shift ;;
        --temperature) TEMPERATURE="$2"; shift ;;
        *) echo "[!] Unknown parameter: $1"; exit 1 ;;
    esac
    shift
done

# Fallback to defaults if unset
MODEL=${MODEL:-$DEFAULT_MODEL}
OUTPUT_DIR=${OUTPUT_DIR:-$DEFAULT_OUTPUT_DIR}
MAX_TOKENS=${MAX_TOKENS:-$DEFAULT_MAX_TOKENS}
TEMPERATURE=${TEMPERATURE:-$DEFAULT_TEMPERATURE}

if [ -z "$PAPERS" ]; then
    echo "[!] No papers specified. Use --papers \"path/to/paper.pdf\" or --papers \"path/to/*.pdf\""
    exit 1
fi

# Expand globs and split into array
IFS=' ' read -ra PDF_LIST <<< "$PAPERS"
EXPANDED_PDFS=()
for pattern in "${PDF_LIST[@]}"; do
    for f in $pattern; do
        EXPANDED_PDFS+=("$f")
    done
done

if [ ${#EXPANDED_PDFS[@]} -eq 0 ]; then
    echo "[!] No PDF files matched the given pattern(s)."
    exit 1
fi

mkdir -p "$OUTPUT_DIR"

# Display configuration summary
echo "===================================="
echo "Starting Tree Parsing"
echo "------------------------------------"
echo "Papers:      ${EXPANDED_PDFS[*]}"
echo "Model:       $MODEL"
echo "Output dir:  $OUTPUT_DIR"
echo "Max tokens:  $MAX_TOKENS"
echo "Temperature: $TEMPERATURE"
echo "===================================="
echo

# ==============================
# Run parser on each paper
# ==============================
TOTAL=${#EXPANDED_PDFS[@]}
SUCCESS=0
FAILED=0

for pdf in "${EXPANDED_PDFS[@]}"; do
    BASENAME=$(basename "$pdf" .pdf)
    OUTPUT_FILE="${OUTPUT_DIR}/${BASENAME}_tree.json"

    echo "===================================================="
    echo "Parsing: $pdf"
    echo "Output:  $OUTPUT_FILE"
    echo "===================================================="

    if python "$PARSER_SCRIPT" "$pdf" \
        --model "$MODEL" \
        --output "$OUTPUT_FILE" \
        --max-tokens "$MAX_TOKENS" \
        --temperature "$TEMPERATURE"; then
        SUCCESS=$((SUCCESS + 1))
    else
        echo "[!] Failed to parse: $pdf"
        FAILED=$((FAILED + 1))
    fi

    echo
done

echo "===================================="
echo "Tree parsing completed"
echo "------------------------------------"
echo "Total:   $TOTAL"
echo "Success: $SUCCESS"
echo "Failed:  $FAILED"
echo "===================================="
