#!/usr/bin/env bash
set -euo pipefail

print_usage() {
    cat <<'EOF'
Run a Windows executable command from WSL with bounded runtime.

Usage:
  run_windows_embedded.sh [--timeout SECONDS] [--log PATH] [--log-only] -- <command> [args...]

Examples:
  run_windows_embedded.sh --timeout 15 -- cargo.exe run --bin fw-lse-submin-mb-stm32 --release
  run_windows_embedded.sh --timeout 20 --log /tmp/fw.log -- probe-rs.exe run --chip STM32U031R8Tx target\thumbv6m-none-eabi\release\fw-lse-submin-mb-stm32
  run_windows_embedded.sh --timeout 30 --log /tmp/fw.log --log-only -- cargo.exe run --bin fw-lse-submin-mb-stm32 --release
EOF
}

timeout_seconds=15
log_path=""
log_only=false

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
            if [[ $# -lt 2 ]]; then
                echo "[embedded-debug] Missing value for $1" >&2
                exit 2
            fi
            log_path="$2"
            shift 2
            ;;
        --log-only)
            log_only=true
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
            echo "[embedded-debug] Unknown option: $1" >&2
            print_usage
            exit 2
            ;;
    esac
done

if ! [[ "$timeout_seconds" =~ ^[0-9]+$ ]] || [[ "$timeout_seconds" -le 0 ]]; then
    echo "[embedded-debug] Timeout must be a positive integer (seconds)." >&2
    exit 2
fi

if [[ $# -eq 0 ]]; then
    echo "[embedded-debug] Missing command after --" >&2
    print_usage
    exit 2
fi

if [[ "$log_only" == true && -z "$log_path" ]]; then
    echo "[embedded-debug] --log-only requires --log <path>." >&2
    exit 2
fi

command_to_run=("$@")

echo "[embedded-debug] Running with ${timeout_seconds}s timeout"
printf '[embedded-debug] Command:'
printf ' %q' "${command_to_run[@]}"
printf '\n'

if [[ -n "$log_path" ]]; then
    mkdir -p "$(dirname "$log_path")"
fi

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

if [[ -n "$log_path" ]]; then
    echo "[embedded-debug] Log saved to $log_path"
fi

if [[ "$status" -eq 124 ]]; then
    echo "[embedded-debug] Timeout reached at ${timeout_seconds}s; treat this as bounded log capture."
    exit 0
fi

if [[ "$status" -ne 0 ]]; then
    echo "[embedded-debug] Command failed with exit code ${status}."
    exit "$status"
fi

echo "[embedded-debug] Command completed without timeout."
