---
name: saleae-logic2-embedded-debug
description: author and run saleae logic 2 automation workflows and logic 2 extensions for embedded projects with connected hardware. use when a coding agent has a local embedded repo, shell access, logic 2 installed, and a connected saleae device, and needs to infer bus or debug signals from firmware, create or modify high level analyzer or measurement extensions, generate or patch capture/export scripts, collect protocol or timing evidence from live hardware, compute metrics from exported captures, or turn one-off bring-up and debugging steps into repeatable workflows.
---

# Saleae Logic 2 Embedded Debug

## Overview
Use this skill to turn firmware context plus connected Saleae hardware into repeatable debug workflows. Default outputs are:

- repo changes under an existing tools or scripts convention such as `tools/saleae/` or `scripts/saleae/`
- capture artifacts under `artifacts/saleae/<timestamp>-<scenario>/`
- a short debug report that ties firmware context to captured evidence

## Default operating rules
1. Treat capture configuration as code. Never rely on whatever Logic 2 currently has open in the UI.
2. Prefer read-only capture first. Only build, flash, reset, or toggle hardware when the repo already defines safe commands or docs for doing so.
3. Always save machine-readable artifacts such as data-table CSV, raw CSV, raw binary, or metrics JSON. Save `.sal` only when replay in Logic 2 will help humans.
4. Always close captures after export so repeated runs do not leak tabs or stale state.
5. Keep reusable scripts and extensions under version control. Keep large artifacts out of Git unless the repo already stores them.
6. Use the smallest workflow that answers the question:
   - protocol semantics on top of I2C, SPI, UART, or Async Serial: HLA
   - numeric metric in the Logic 2 UI over a selected range: measurement extension
   - live capture, export, or regression: automation script
7. If channel mapping is incomplete, derive the best mapping from repo symbols, schematics, README files, pin headers, devicetree, board config, and recent commits. Record every assumption explicitly in the report and script comments.

## Workflow decision tree
1. Need a custom protocol view on top of I2C, SPI, UART, or Async Serial? Read `references/extension-playbook.md` and scaffold an HLA with:
   ```bash
   python3 scripts/scaffold_extension.py --kind hla --display-name "Sensor Frames" --output /tmp/sensor-frames
   ```
2. Need a numeric metric inside Logic 2 such as clock jitter, pulse width, duty cycle, min or max voltage, or peak-to-peak voltage? Read `references/extension-playbook.md` and scaffold a measurement extension.
3. Need live debugging, bring-up, or regression capture against connected hardware? Read `references/automation-playbook.md`, validate the environment and the Python package with:
   ```bash
   python3 scripts/check_logic2_env.py
   ```
   then create or patch an automation script from `assets/templates/automation/`.
4. Need sample-rate, jitter, latency, or utilization metrics from protocol events? Export a data table or timestamp CSV, then run:
   ```bash
   python3 scripts/saleae_interval_metrics.py --csv path/to/export.csv --time-column "Time [s]"
   ```
5. Need a one-off investigation tied to firmware changes? Diff the driver or protocol code first, design the capture around the changed signals, then collect evidence.

## Repo-first discovery
Before writing code, inspect the repo for:

- bus type, nominal speed, and framing rules
- signal names and channel candidates such as `SCL`, `SDA`, `CS`, `CLK`, `MISO`, `MOSI`, `RX`, `TX`, `IRQ`, `DRDY`, `RST`, and power-good
- device addresses, command opcodes, register maps, packet structs, enums, and CRC rules
- existing build, flash, reset, and test scripts
- serial logging, RTT, or console tooling that can be correlated with captures
- prior Saleae, sigrok, oscilloscope, or hardware test utilities

Good places to search:

- board support package, board config, devicetree, pinmux, HAL init, sensor and driver source, test fixtures, README and setup docs, CI hardware jobs, recent commits, and recent PRs

## Standard live-debug workflow
1. Run `python3 scripts/check_logic2_env.py` from the skill folder or copy it into the repo and run it there. If the `logic2-automation` package is missing in the active Python environment, create or reuse a repo-local virtualenv and install it before writing capture code.
2. Create `artifacts/saleae/<timestamp>-<scenario>/`.
3. Choose or create an automation script from `assets/templates/automation/`.
4. Fill in explicit device selection, digital and analog channels, sample rates, trigger mode, analyzer settings, export paths, and report paths.
5. If safe and useful, pair the capture with build, flash, reset, or serial commands from the repo.
6. Export at least one machine-readable artifact and one short report.
7. If the workflow should be reused, keep the script in the repo and add minimal usage notes.

## Extension authoring workflow
1. Decide the extension type:
   - HLA when built-in analyzers already produce the low-level frames you need.
   - Digital measurement when the result is a number derived from digital transitions over a selected range.
   - Analog measurement when the result is a number derived from analog samples over a selected range.
2. Scaffold with `scripts/scaffold_extension.py`.
3. Keep protocol math and state in pure helper functions or methods that can be unit-tested outside Logic 2.
4. Derive field names, enums, register names, and state-machine labels from the repo, not ad-hoc labels.
5. Prefer stable, machine-readable frame data keys so exported tables are easy to post-process.
6. Validate the extension against at least one known-good capture or fixture.
7. Document installation, expected input analyzer, and known limits in the extension README.

## Timing metrics workflow
For achieved sample rate, jitter, latency, or utilization:

1. Identify the event that corresponds to one sample or transaction:
   - sensor data-ready IRQ edge
   - I2C read of the sample register
   - SPI burst completion
   - HLA-emitted semantic frame such as `sample`
2. Export timestamps for those events.
3. Run `scripts/saleae_interval_metrics.py` on the exported CSV.
4. Report event count, achieved mean rate, interval min, mean, max, standard deviation, p95 and p99 interval, peak-to-peak jitter, and any obvious multimodal or dropped-sample behavior.
5. If results look wrong, capture a wider context and correlate with reset lines, IRQs, or power or analog channels.

## Output expectations
Use this default report structure unless the repo already has one:

# Saleae debug summary

## Goal
What question the capture was meant to answer.

## Firmware context
Relevant files, commits, settings, addresses, and assumptions.

## Capture plan
Channels, sample rates, trigger mode, analyzers, and why they were chosen.

## Artifacts
Paths to scripts, exports, `.sal` files, logs, and generated metrics.

## Findings
Concrete evidence from the capture.

## Next actions
Smallest high-value follow-up steps.

## Resources
- `references/automation-playbook.md` — capture architecture, triggers, artifacts, mixed-signal guidance, and timing-metrics advice.
- `references/extension-playbook.md` — when to use HLA vs measurement, extension design rules, and testing strategy.
- `references/embedded-debug-recipes.md` — ready-made embedded workflows for bring-up, sensor timing, bus errors, and regression capture.
- `assets/templates/automation/` — starter automation scripts for common debug tasks.
- `scripts/check_logic2_env.py` — detect Logic 2, automation port, and repo context.
- `scripts/scaffold_extension.py` — generate HLA or measurement extension skeletons.
- `scripts/saleae_interval_metrics.py` — compute interval, rate, and jitter stats from exported CSV timestamps.
