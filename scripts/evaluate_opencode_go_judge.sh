#!/bin/bash
set -euxCo pipefail
cd "$(dirname "$0")"

function usage() {
  cat <<'EOF' >&2
Description:
    Run missing OpenCode Go agent logs, then evaluate them with selected judge models.

Usage:
    scripts/evaluate_opencode_go_judge.sh [OPTIONS] [MODEL...]

Options:
    --judge-model MODEL: judge model. Can be repeated.
    --repair-model MODEL: JSON repair model. Default: same as each judge model.
    --eval-only: do not run missing agent logs.
    --overwrite: replace existing results intentionally.
    --help, -h: print this.

Examples:
    scripts/evaluate_opencode_go_judge.sh
    scripts/evaluate_opencode_go_judge.sh glm-5.1 minimax-m2.7 mimo-v2.5-pro
    scripts/evaluate_opencode_go_judge.sh --judge-model qwen3.6-plus glm-5.1
    scripts/evaluate_opencode_go_judge.sh --overwrite

Default pairs:
    deepseek-v4-pro   -> qwen3.6-plus
    deepseek-v4-flash -> qwen3.6-plus
    kimi-k2.6         -> qwen3.6-plus

Output:
    results/<evaluated-model>/<judge-model>/<task>.json
EOF
  exit 1
}

readonly ROOT_DIR=".."
readonly AGENT_ID="opencode_go"
readonly DEFAULT_JUDGE_MODELS=(
  "qwen3.6-plus"
)
readonly DEFAULT_MODELS=(
  "deepseek-v4-pro"
  "deepseek-v4-flash"
  "kimi-k2.6"
)
readonly DEFAULT_EVALUATION_PAIRS=(
  "deepseek-v4-pro qwen3.6-plus"
  "deepseek-v4-flash qwen3.6-plus"
  "kimi-k2.6 qwen3.6-plus"
)
readonly TASK_IDS=(
  "questbench"
  "counterfactual_simulatability"
  "cot_in_planning"
  "awareness_detection"
  "llms_assume_rationality"
)

repair_model=""
eval_only="0"
overwrite="0"
judge_models=()
models=()
evaluation_pairs=()
use_default_pairs="1"
failures=()

function latest_completed_timestamp() {
  local _model="$1"
  local _task_id="$2"
  local _log_dir="${ROOT_DIR}/log/${AGENT_ID}/${_model}/${_task_id}"
  local _log_path=""

  if [[ ! -d "${_log_dir}" ]]; then
    return 1
  fi

  _log_path="$(grep -rl '"result"' "${_log_dir}" --include='log.log' | sort | tail -1 || true)"
  if [[ -z "${_log_path}" ]]; then
    return 1
  fi

  basename "$(dirname "${_log_path}")"
}

function result_path() {
  local _model="$1"
  local _judge_model="$2"
  local _task_id="$3"
  echo "${ROOT_DIR}/results/${_model}/${_judge_model}/${_task_id}.json"
}

function parse_args() {
  while [[ "$#" -gt 0 ]]; do
    case "$1" in
    --judge-model)
      if [[ -z "${2:-}" ]]; then
        usage
      fi
      judge_models+=("$2")
      use_default_pairs="0"
      shift 2
      ;;
    --repair-model)
      if [[ -z "${2:-}" ]]; then
        usage
      fi
      repair_model="$2"
      shift 2
      ;;
    --eval-only)
      eval_only="1"
      shift
      ;;
    --overwrite)
      overwrite="1"
      shift
      ;;
    --help | -h)
      usage
      ;;
    --*)
      usage
      ;;
    *)
      models+=("$1")
      use_default_pairs="0"
      shift
      ;;
    esac
  done

  build_evaluation_pairs
}

function append_evaluation_pair() {
  local _model="$1"
  local _judge_model="$2"

  if [[ "${_model}" == "${_judge_model}" ]]; then
    echo "Skipping self-judge pair: model=${_model} judge=${_judge_model}" >&2
    return
  fi

  evaluation_pairs+=("${_model} ${_judge_model}")
}

function build_evaluation_pairs() {
  local _judge_model
  local _model

  if [[ "${use_default_pairs}" == "1" ]]; then
    evaluation_pairs=("${DEFAULT_EVALUATION_PAIRS[@]}")
    return
  fi

  if [[ "${#judge_models[@]}" -eq 0 ]]; then
    judge_models=("${DEFAULT_JUDGE_MODELS[@]}")
  fi

  if [[ "${#models[@]}" -eq 0 ]]; then
    models=("${DEFAULT_MODELS[@]}")
  fi

  for _model in "${models[@]}"; do
    for _judge_model in "${judge_models[@]}"; do
      append_evaluation_pair "${_model}" "${_judge_model}"
    done
  done

  if [[ "${#evaluation_pairs[@]}" -eq 0 ]]; then
    echo "No non-self evaluation pairs selected." >&2
    exit 1
  fi
}

function require_api_key() {
  if [[ -f "${ROOT_DIR}/.env" ]]; then
    set -a
    # shellcheck source=/dev/null
    source "${ROOT_DIR}/.env"
    set +a
  fi

  if [[ -z "${OPENCODE_API_KEY:-}" ]]; then
    echo "OPENCODE_API_KEY is required." >&2
    exit 1
  fi
}

function run_agent_task() {
  local _model="$1"
  local _task_id="$2"

  (
    cd "${ROOT_DIR}"
    AGENT_ID="${AGENT_ID}" \
      TASK_ID="${_task_id}" \
      LLM_MODEL="${_model}" \
      uv run --frozen python agents/opencode_go/run.py
  )
}

function completed_timestamp_or_run() {
  local _model="$1"
  local _task_id="$2"
  local _timestamp=""

  if _timestamp="$(latest_completed_timestamp "${_model}" "${_task_id}")"; then
    echo "${_timestamp}"
    return
  fi

  if [[ "${eval_only}" == "1" ]]; then
    echo "Skipping missing completed log: model=${_model} task=${_task_id}" >&2
    return 1
  fi

  if ! run_agent_task "${_model}" "${_task_id}" >&2; then
    echo "Agent run failed: model=${_model} task=${_task_id}" >&2
    return 1
  fi

  if ! _timestamp="$(latest_completed_timestamp "${_model}" "${_task_id}")"; then
    echo "Agent run did not produce a completed log: model=${_model} task=${_task_id}" >&2
    return 1
  fi

  echo "${_timestamp}"
}

function record_failure() {
  local _model="$1"
  local _judge_model="$2"
  local _task_id="$3"
  local _stage="$4"

  failures+=("${_model} ${_judge_model} ${_task_id} ${_stage}")
}

function report_failures() {
  local _failure

  if [[ "${#failures[@]}" -eq 0 ]]; then
    return
  fi

  echo "Failed items:" >&2
  for _failure in "${failures[@]}"; do
    echo "  ${_failure}" >&2
  done
  exit 1
}

function evaluate_one() {
  local _model="$1"
  local _task_id="$2"
  local _timestamp="$3"
  local _judge_model="$4"
  local _repair_model="${repair_model:-${_judge_model}}"

  if [[ "${overwrite}" == "1" ]]; then
    (
      cd "${ROOT_DIR}"
      uv run --frozen python eval/opencode_go_eval.py \
        --agent "${AGENT_ID}" \
        --model "${_model}" \
        --task "${_task_id}" \
        --timestamp "${_timestamp}" \
        --judge-model "${_judge_model}" \
        --repair-model "${_repair_model}" \
        --overwrite
    )
    return
  fi

  (
    cd "${ROOT_DIR}"
    uv run --frozen python eval/opencode_go_eval.py \
      --agent "${AGENT_ID}" \
      --model "${_model}" \
      --task "${_task_id}" \
      --timestamp "${_timestamp}" \
      --judge-model "${_judge_model}" \
      --repair-model "${_repair_model}"
  )
}

function main() {
  local _judge_model
  local _model
  local _pair
  local _path
  local _task_id
  local _timestamp

  parse_args "$@"
  require_api_key

  for _pair in "${evaluation_pairs[@]}"; do
    read -r _model _judge_model <<<"${_pair}"

    for _task_id in "${TASK_IDS[@]}"; do
      _path="$(result_path "${_model}" "${_judge_model}" "${_task_id}")"
      if [[ "${overwrite}" != "1" && -f "${_path}" ]]; then
        echo "Skipping existing result: ${_path}" >&2
        continue
      fi

      if ! _timestamp="$(completed_timestamp_or_run "${_model}" "${_task_id}")"; then
        record_failure "${_model}" "${_judge_model}" "${_task_id}" "agent"
        continue
      fi

      if ! evaluate_one "${_model}" "${_task_id}" "${_timestamp}" "${_judge_model}"; then
        record_failure "${_model}" "${_judge_model}" "${_task_id}" "eval"
        continue
      fi
    done
  done

  report_failures
}

main "$@"
