#!/bin/bash
set -euxCo pipefail

cd "$(dirname "$0")/.."

if [[ -f .env ]]; then
  set -a
  source .env
  set +a
fi

readonly OUTER_AGENT_ID="opencode_go"
readonly OUTER_MODEL="${OUTER_MODEL:-deepseek-v4-pro}"
readonly JUDGE_MODEL="${JUDGE_MODEL:-qwen3.6-plus}"
readonly REPAIR_MODEL="${REPAIR_MODEL:-${JUDGE_MODEL}}"
readonly SKIP_COMPLETED="${SKIP_COMPLETED:-1}"
readonly FORCE_RERUN="${FORCE_RERUN:-0}"
readonly TASK_IDS=(
  "questbench"
  "counterfactual_simulatability"
  "cot_in_planning"
  "awareness_detection"
  "llms_assume_rationality"
)

usage() {
  cat <<'USAGE'
Run the OpenCode Go-only FIRE-Bench subset.

Environment:
  OPENCODE_API_KEY   Required.
  OUTER_MODEL        Optional. Default: deepseek-v4-pro.
  JUDGE_MODEL        Optional. Default: qwen3.6-plus.
  REPAIR_MODEL       Optional. Default: same as JUDGE_MODEL.
  SKIP_COMPLETED     Optional. Default: 1.
  FORCE_RERUN        Optional. Default: 0. Set to 1 to ignore completed logs.

Usage:
  scripts/run_opencode_go_subset.sh
USAGE
}

function latest_completed_log() {
  local _task_id="$1"
  local _log_dir="log/${OUTER_AGENT_ID}/${OUTER_MODEL}/${_task_id}"
  if [[ ! -d "${_log_dir}" ]]; then
    return 1
  fi
  grep -rl '"result"' "${_log_dir}" --include='log.log' | sort | tail -1
}

function timestamp_from_log_path() {
  local _log_path="$1"
  basename "$(dirname "${_log_path}")"
}

function eval_result_path() {
  local _task_id="$1"
  local _timestamp="$2"
  echo "results/opencode_go_eval_${OUTER_AGENT_ID}_${OUTER_MODEL}_${_task_id}_${_timestamp}.json"
}

function run_task() {
  local _task_id="$1"
  AGENT_ID="${OUTER_AGENT_ID}" \
    TASK_ID="${_task_id}" \
    LLM_MODEL="${OUTER_MODEL}" \
    uv run --frozen python agents/opencode_go/run.py
}

function evaluate_task() {
  local _task_id="$1"
  local _timestamp="$2"
  uv run --frozen python eval/opencode_go_eval.py \
    --agent "${OUTER_AGENT_ID}" \
    --model "${OUTER_MODEL}" \
    --task "${_task_id}" \
    --timestamp "${_timestamp}" \
    --judge-model "${JUDGE_MODEL}" \
    --repair-model "${REPAIR_MODEL}"
}

if [[ "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

if [[ -z "${OPENCODE_API_KEY:-}" ]]; then
  echo "OPENCODE_API_KEY is required." >&2
  exit 1
fi

for task_id in "${TASK_IDS[@]}"; do
  completed_log=""
  if [[ "${FORCE_RERUN}" != "1" && "${SKIP_COMPLETED}" == "1" ]]; then
    completed_log="$(latest_completed_log "${task_id}" || true)"
  fi

  if [[ -n "${completed_log}" ]]; then
    echo "Skipping completed task: ${task_id} (${completed_log})"
    timestamp="$(timestamp_from_log_path "${completed_log}")"
  else
    run_task "${task_id}"

    log_path="$(find "log/${OUTER_AGENT_ID}/${OUTER_MODEL}/${task_id}" -name log.log -type f | sort | tail -1)"
    timestamp="$(timestamp_from_log_path "${log_path}")"
  fi

  result_path="$(eval_result_path "${task_id}" "${timestamp}")"
  if [[ "${FORCE_RERUN}" != "1" && "${SKIP_COMPLETED}" == "1" && -f "${result_path}" ]]; then
    echo "Skipping completed evaluation: ${result_path}"
    continue
  fi

  evaluate_task "${task_id}" "${timestamp}"
done
