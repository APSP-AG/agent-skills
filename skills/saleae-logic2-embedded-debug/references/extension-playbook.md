# Extension playbook

## Choose the extension type

### High-Level Analyzer
Choose an HLA when the built-in analyzer already understands the physical or link layer and you want a richer semantic view.

Best fits:
- protocol on top of I2C, SPI, UART, or Async Serial
- register transactions turned into named operations
- framing, state, CRC, or field interpretation on top of decoded bytes
- semantic events like `sample`, `fifo_overrun`, or `calibration_done`

Avoid HLA when:
- you need raw edge-level decoding from an unsupported protocol
- the built-in analyzer cannot produce the frames you need

### Digital measurement
Choose a digital measurement when the user wants a number over a selected range in the Logic 2 UI.

Best fits:
- clock frequency or period stats
- duty cycle
- edge count
- pulse width
- timing jitter over a selected window

### Analog measurement
Choose an analog measurement when the result is a numeric summary of analog samples over a selected range.

Best fits:
- min, max, RMS, peak-to-peak
- settling time surrogate metrics
- overshoot, undershoot, or ripple-derived measurements


## Python compatibility
Logic 2 executes extension code with its embedded Python runtime. Keep generated extension code compatible with Python 3.8 syntax and standard library behavior. Avoid newer language features in HLAs and measurement files unless you have confirmed the installed Logic 2 version supports them.

## HLA design rules
1. Derive names from the repo. Use real register names, opcode names, frame names, and enum labels.
2. Keep parsing logic separate from Saleae plumbing. The HLA class should be thin.
3. Emit stable frame types and stable data keys. Favor keys like `address`, `register`, `direction`, `payload`, `status`, and `summary`.
4. Include a compact human display string in `result_types`, but keep the raw data rich enough for export.
5. Make state machines explicit. Track incomplete transactions across frames instead of doing brittle one-frame-only logic.
6. When the protocol spans multiple lower-level frames, buffer until the semantic unit is complete, then emit one semantic frame.

## Measurement design rules
1. Return values in canonical base units. Let the Logic UI apply prefixes.
2. Use descriptive metric keys; the key must stay stable because it is part of the extension contract.
3. Accumulate state during `process_data`, compute the final metric in `measure`.
4. For digital measurements, remember the first entry indicates the starting state and time of the selected range, not necessarily a transition.
5. For analog measurements, assume `process_data` may receive multiple chunks.

## Minimal extension layout
A good local extension folder usually contains:

```text
my-extension/
  extension.json
  README.md
  HighLevelAnalyzer.py        # for HLA
  DigitalMeasurement.py       # for digital measurement
  AnalogMeasurement.py        # for analog measurement
```

One extension package can contain more than one extension class if that helps keep related tools together.

## Authoring workflow
1. Scaffold with `scripts/scaffold_extension.py`.
2. Patch the generated files with repo-specific field names and behavior.
3. If the extension is tied to one driver or one sensor family, keep a short note in the README naming the firmware files that define the protocol.
4. Validate with one known-good capture before using the extension for debugging.
5. If the extension is generally useful, keep it in a dedicated repo subdirectory and document installation.

## Testing strategy

### HLA testing
Use two layers:
- unit tests for pure helper functions and state-machine helpers
- manual or scripted integration checks in Logic 2 against known captures

Good fixture sources:
- existing Saleae exports
- firmware integration tests that know the expected byte stream
- register transactions copied from datasheets and adapted to repo names

### Measurement testing
Use numeric fixtures when possible:
- synthetic edge times for digital metrics
- synthetic numpy sample arrays for analog metrics

Even if the final Logic 2 integration is manual, the core math should be testable outside Logic.

## Installation notes
A local extension can be loaded from its `extension.json` file inside Logic 2. Keep the extension self-contained so another engineer can load it without additional hidden files.

## Common embedded patterns

### HLA examples
- decode I2C register reads into named sensor fields
- interpret SPI command and response packets into semantic messages
- convert UART boot protocol traffic into command names and error reasons
- collapse verbose low-level frames into one `sample` event for timing analysis

### Measurement examples
- digital jitter measurement over a clock or IRQ line
- digital pulse width stats for a strobe or frame-sync signal
- analog rail droop measurement during radio transmit or sensor startup
- analog ripple measurement over a selected power window
