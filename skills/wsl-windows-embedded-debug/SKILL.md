---
name: wsl-windows-embedded-debug
description: Run embedded build/flash/debug workflows from WSL by invoking Windows executables that own USB/JTAG access (for example `cargo.exe`, `probe-rs.exe`, or `openocd.exe`). Use when an agent must reproduce firmware behavior on hardware, flash an MCU, collect bounded runtime logs, or debug probe connectivity from a WSL workspace.
---

# WSL Windows Embedded Debug

## Overview

Use Windows-side toolchains from WSL so code stays in the Linux workspace while USB-capable flashing and runtime logging happen through Windows executables.

## Core Workflow

1. Confirm that the hardware step needs Windows USB access.
2. Run the command through `scripts/run_windows_embedded.sh`.
3. Use a bounded timeout to capture useful logs quickly.
4. Treat timeout exit `124` as expected log capture, not automatic failure.
5. Iterate with adjusted timeout, bin target, and command flags.

## Run Commands

Use this wrapper as the default execution path:

```bash
./scripts/run_windows_embedded.sh --timeout 15 -- cargo.exe run --bin fw-lse-submin-mb-stm32 --release
```

Capture logs to a file for later inspection:

```bash
./scripts/run_windows_embedded.sh --timeout 20 --log /tmp/fw-run.log -- cargo.exe run --bin fw-lse-submin-mb-stm32 --release
```

Use log-only mode when log frequency is high and terminal/context noise is expensive:

```bash
./scripts/run_windows_embedded.sh --timeout 20 --log /tmp/fw-run.log --log-only -- cargo.exe run --bin fw-lse-submin-mb-stm32 --release
```

Pass any Windows executable command after `--` (for example `probe-rs.exe run ...`, `openocd.exe ...`, or vendor CLI tools).

## Choose Output Mode

Agents should intentionally choose output mode based on expected verbosity and run duration:

- Use raw terminal output for short, low-frequency logs where live feedback is valuable.
- Use `--log` for balanced runs that need both live stream and saved artifacts.
- Use `--log --log-only` for noisy/long sessions to avoid blowing context while preserving complete logs for targeted inspection.

`--log-only` is an intended first-class option, not a workaround.

## Interpret Exit Codes

- `0`: Command completed before timeout.
- `124`: Timeout reached; treat as successful bounded capture for long-running firmware sessions.
- Any other non-zero code: Treat as a real error and debug.

## Debug Loop

1. Start with 10–20 second timeout.
2. Confirm flash + early boot logs appear.
3. Increase timeout only when deeper runtime phases are needed.
4. Keep command explicit (`--bin`, `--release`, feature flags).
5. Repeat with focused changes between runs.

## Troubleshoot

- If `cargo.exe` is missing, verify Windows Rust toolchain installation and PATH exposure to WSL.
- If flashing fails with probe errors, verify the device is visible to Windows and no other process owns the probe.
- If no runtime logs appear, confirm logger transport settings and runtime command configuration.

Use `references/wsl-windows-embedded-troubleshooting.md` for detailed checks and alternatives.
