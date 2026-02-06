# WSL + Windows Embedded Troubleshooting

## Preconditions

1. Run from the firmware project directory in WSL.
2. Use Windows executables (`*.exe`) for steps that require USB/JTAG access.
3. Keep Windows-side toolchains installed (for example Rust, probe-rs, OpenOCD, vendor tools).

## Known-Good Command Pattern

Use this baseline first:

```bash
timeout 15s cargo.exe run --bin fw-lse-submin-mb-stm32 --release
```

Prefer the wrapper script for repeatable runs:

```bash
./scripts/run_windows_embedded.sh --timeout 15 -- cargo.exe run --bin fw-lse-submin-mb-stm32 --release
```

Use log-only mode when firmware logs are very verbose:

```bash
./scripts/run_windows_embedded.sh --timeout 15 --log /tmp/fw.log --log-only -- cargo.exe run --bin fw-lse-submin-mb-stm32 --release
```

## Error Patterns

### `cargo.exe: command not found`

- Install Rust on Windows.
- Ensure Windows Cargo path is available from WSL (for example via `/mnt/c/Users/<user>/.cargo/bin` in PATH).

### Probe/flash access errors

- Confirm the debug probe is visible in Windows Device Manager.
- Close other tools that may own the probe (IDE, another `probe-rs`, vendor monitor).
- Retry with only one flashing process active.

### Build succeeds but no target logs

- Confirm the runtime logger path is enabled (RTT/defmt/UART) in firmware.
- Confirm the command used actually starts execution (`cargo.exe run` vs build-only steps).
- Increase timeout if startup and calibration take longer than expected.

## Debugging Tactics

1. Start with short timeout (10–20 seconds) to verify flashing and boot.
2. Capture logs to a file with `--log` for comparisons across runs.
3. Switch to `--log --log-only` when terminal noise is high and then inspect with `tail`/`rg`.
4. Change one parameter at a time (timeout, feature flags, bin target).
5. Preserve the exact command in notes for reproducibility.

## Alternative Architectures to Explore

- Attach USB devices directly into WSL with `usbipd-win` to use Linux-native tools.
- Run flashing through a small Windows-side runner service and call it from WSL.
- Split workflow: build in WSL, flash with Windows command wrappers.
