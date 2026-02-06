#!/usr/bin/env bash
set -euo pipefail

print_usage() {
    cat <<'EOF'
Run a Windows executable command from WSL with bounded runtime.

Usage:
  run_windows_embedded.sh [--timeout SECONDS] [--log PATH] [--log-only] [--artifacts-dir PATH] [--tail LINES] [--check] -- <command> [args...]
  run_windows_embedded.sh [--check]

Examples:
  run_windows_embedded.sh --timeout 15 -- cargo.exe run --bin fw-lse-submin-mb-stm32 --release
  run_windows_embedded.sh --timeout 20 --log /tmp/fw.log -- probe-rs.exe run --chip STM32U031R8Tx target\thumbv6m-none-eabi\release\fw-lse-submin-mb-stm32
  run_windows_embedded.sh --timeout 30 --log /tmp/fw.log --log-only -- cargo.exe run --bin fw-lse-submin-mb-stm32 --release
  run_windows_embedded.sh --timeout 30 --artifacts-dir /tmp/fw-run --log-only --tail 30 -- cargo.exe run --bin fw-lse-submin-mb-stm32 --release
  run_windows_embedded.sh --check -- cargo.exe run --bin fw-lse-submin-mb-stm32 --release
EOF
}

fail_with_usage() {
    local message="$1"
    echo "[embedded-debug] $message" >&2
    print_usage
    exit 2
}

render_command() {
    local rendered=""
    printf -v rendered '%q ' "$@"
    rendered="${rendered% }"
    printf '%s' "$rendered"
}

json_escape() {
    local value="$1"
    value="${value//\\/\\\\}"
    value="${value//\"/\\\"}"
    value="${value//$'\n'/\\n}"
    value="${value//$'\r'/\\r}"
    value="${value//$'\t'/\\t}"
    printf '%s' "$value"
}

run_preflight_checks() {
    local failures=0
    local command_name="$1"

    if command -v timeout >/dev/null 2>&1; then
        echo "[embedded-debug][check] PASS timeout command found"
    else
        echo "[embedded-debug][check] FAIL timeout command not found"
        failures=$((failures + 1))
    fi

    if [[ -n "$command_name" ]]; then
        if command -v "$command_name" >/dev/null 2>&1; then
            echo "[embedded-debug][check] PASS target command '$command_name' found"
        else
            echo "[embedded-debug][check] FAIL target command '$command_name' not found"
            failures=$((failures + 1))
        fi
    else
        echo "[embedded-debug][check] PASS no target command supplied (environment-only check)"
    fi

    local current_dir
    current_dir="$(pwd)"
    if [[ -d "$current_dir" ]]; then
        echo "[embedded-debug][check] PASS working directory exists: $current_dir"
    else
        echo "[embedded-debug][check] FAIL working directory missing: $current_dir"
        failures=$((failures + 1))
    fi

    if [[ -n "$log_path" ]]; then
        local log_dir
        log_dir="$(dirname "$log_path")"
        if mkdir -p "$log_dir" 2>/dev/null; then
            if touch "$log_path" 2>/dev/null; then
                echo "[embedded-debug][check] PASS log path writable: $log_path"
            else
                echo "[embedded-debug][check] FAIL log path not writable: $log_path"
                failures=$((failures + 1))
            fi
        else
            echo "[embedded-debug][check] FAIL cannot create log directory: $log_dir"
            failures=$((failures + 1))
        fi
    fi

    if [[ -n "$artifacts_dir" ]]; then
        if mkdir -p "$artifacts_dir" 2>/dev/null; then
            echo "[embedded-debug][check] PASS artifacts directory ready: $artifacts_dir"
        else
            echo "[embedded-debug][check] FAIL cannot create artifacts directory: $artifacts_dir"
            failures=$((failures + 1))
        fi
    fi

    if [[ "$failures" -eq 0 ]]; then
        echo "[embedded-debug][check] All checks passed."
        return 0
    fi

    echo "[embedded-debug][check] Found $failures issue(s)."
    return 1
}

timeout_seconds=15
log_path=""
log_only=false
artifacts_dir=""
tail_lines=0
check_only=false

if [[ $# -eq 0 ]]; then
    print_usage
    exit 2
fi

while [[ $# -gt 0 ]]; do
    case "$1" in
        -t|--timeout)
            if [[ $# -lt 2 ]]; then
                echo "[embedded-debug] Missing value for $1" >&2
                exit 2
            fi
            timeout_seconds="$2"
            shift 2
            ;;
        -l|--log)
            [[ $# -lt 2 ]] && fail_with_usage "Missing value for $1"
            log_path="$2"
            shift 2
            ;;
        --log-only)
            log_only=true
            shift
            ;;
        --artifacts-dir)
            [[ $# -lt 2 ]] && fail_with_usage "Missing value for $1"
            artifacts_dir="$2"
            shift 2
            ;;
        --tail)
            [[ $# -lt 2 ]] && fail_with_usage "Missing value for $1"
            tail_lines="$2"
            shift 2
            ;;
        --check)
            check_only=true
            shift
            ;;
        -h|--help)
            print_usage
            exit 0
            ;;
        --)
            shift
            break
            ;;
        *)
            fail_with_usage "Unknown option: $1"
            ;;
    esac
done

if ! [[ "$timeout_seconds" =~ ^[0-9]+$ ]] || [[ "$timeout_seconds" -le 0 ]]; then
    fail_with_usage "Timeout must be a positive integer (seconds)."
fi

if ! [[ "$tail_lines" =~ ^[0-9]+$ ]]; then
    fail_with_usage "Tail lines must be a non-negative integer."
fi

if [[ -n "$artifacts_dir" ]]; then
    mkdir -p "$artifacts_dir"
fi

if [[ -z "$log_path" && -n "$artifacts_dir" ]]; then
    log_path="$artifacts_dir/run.log"
fi

if [[ "$log_only" == true && -z "$log_path" ]]; then
    fail_with_usage "--log-only requires --log <path> or --artifacts-dir <path>."
fi

if [[ "$tail_lines" -gt 0 && -z "$log_path" ]]; then
    fail_with_usage "--tail requires --log <path> or --artifacts-dir <path>."
fi

if [[ -n "$log_path" ]]; then
    mkdir -p "$(dirname "$log_path")"
fi

command_to_run=("$@")

if [[ "$check_only" == false && "${#command_to_run[@]}" -eq 0 ]]; then
    fail_with_usage "Missing command after --"
fi

command_name=""
if [[ "${#command_to_run[@]}" -gt 0 ]]; then
    command_name="${command_to_run[0]}"
fi

if [[ "$check_only" == true ]]; then
    run_preflight_checks "$command_name"
    exit $?
fi

echo "[embedded-debug] Running with ${timeout_seconds}s timeout"
printf '[embedded-debug] Command:'
printf ' %q' "${command_to_run[@]}"
printf '\n'

started_at_utc="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
started_epoch="$(date +%s)"

set +e
if [[ -n "$log_path" ]]; then
    if [[ "$log_only" == true ]]; then
        timeout "${timeout_seconds}s" "${command_to_run[@]}" >"$log_path" 2>&1
        status=$?
    else
        timeout "${timeout_seconds}s" "${command_to_run[@]}" 2>&1 | tee "$log_path"
        status=${PIPESTATUS[0]}
    fi
else
    timeout "${timeout_seconds}s" "${command_to_run[@]}"
    status=$?
fi
set -e

ended_at_utc="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
ended_epoch="$(date +%s)"
duration_seconds=$((ended_epoch - started_epoch))

if [[ -n "$log_path" ]]; then
    echo "[embedded-debug] Log saved to $log_path"
fi

result_status="ok"
normalized_exit_code="$status"
timed_out=false

if [[ "$status" -eq 124 ]]; then
    result_status="timeout"
    normalized_exit_code=0
    timed_out=true
elif [[ "$status" -ne 0 ]]; then
    result_status="error"
fi

if [[ -n "$artifacts_dir" ]]; then
    command_rendered="$(render_command "${command_to_run[@]}")"
    cwd_rendered="$(pwd)"
    log_path_rendered="$log_path"
    run_json_path="$artifacts_dir/run.json"
    cat >"$run_json_path" <<EOF
{
  "command": "$(json_escape "$command_rendered")",
  "cwd": "$(json_escape "$cwd_rendered")",
  "timeout_seconds": $timeout_seconds,
  "started_at_utc": "$(json_escape "$started_at_utc")",
  "ended_at_utc": "$(json_escape "$ended_at_utc")",
  "duration_seconds": $duration_seconds,
  "status": "$(json_escape "$result_status")",
  "raw_exit_code": $status,
  "normalized_exit_code": $normalized_exit_code,
  "timed_out": $timed_out,
  "log_path": "$(json_escape "$log_path_rendered")"
}
EOF
    echo "[embedded-debug] Run metadata saved to $run_json_path"
fi

if [[ "$tail_lines" -gt 0 && -n "$log_path" ]]; then
    if [[ -f "$log_path" ]]; then
        echo "[embedded-debug] Tail preview (${tail_lines} lines):"
        tail -n "$tail_lines" "$log_path"
    else
        echo "[embedded-debug] Tail requested but log file not found: $log_path"
    fi
fi

if [[ "$result_status" == "timeout" ]]; then
    echo "[embedded-debug] Timeout reached at ${timeout_seconds}s; treat this as bounded log capture."
    exit 0
fi

if [[ "$result_status" == "error" ]]; then
    echo "[embedded-debug] Command failed with exit code ${status}."
    exit "$status"
fi

echo "[embedded-debug] Command completed without timeout."
