# Automation playbook

## Core model
Treat Logic 2 automation as a file-producing instrument workflow:

1. ensure the active Python environment can import `saleae.automation`
2. connect to or launch Logic 2
3. define the capture configuration explicitly
4. run the capture
5. add analyzers and optionally HLAs
6. export machine-readable artifacts
7. compute metrics outside Logic 2
8. close the capture

The most reliable pattern is `capture -> export -> analyze`, not real-time streaming analysis.

## Python environment
Use a repo-local virtual environment when possible. If `python3 scripts/check_logic2_env.py` reports that the automation package is missing, install it with:

```bash
pip install logic2-automation
```

Keep automation scripts and their dependencies close to the repo so other engineers can reproduce the workflow.

## Choosing a capture mode

### Timed capture
Use for smoke tests, rate checks, boot windows, and repeated regression runs.

Pick timed capture when:
- the interesting behavior always happens within a known window
- you want deterministic artifact sizes
- you plan to run the same capture in CI or after every firmware flash

### Manual capture
Use when an external action determines when to stop, such as a device-side fault, an operator step, or a shell command that reproduces the issue.

Pick manual capture when:
- the exact stop time is not known ahead of time
- you want to keep a rolling history and stop on a fault
- you are coordinating multiple bench tools

### Digital trigger capture
Use when a digital line marks the event of interest.

Pick trigger capture when:
- an IRQ, DRDY, CS, or RESET edge marks the beginning of the interesting region
- you need a narrow post-trigger window
- the fault is rare and you do not want huge artifacts

## Artifact strategy

### Always create machine-readable output
Prefer one or more of:
- analyzer data-table CSV for decoded protocol events
- raw CSV for simple inspection
- raw binary for large captures or heavy post-processing
- metrics JSON or Markdown summaries produced by your scripts

### Save `.sal` only when it helps humans
A `.sal` file is valuable for replay in Logic 2, screenshots, or handoff to another engineer. It should be optional for automated workflows.

### Recommended directory layout
Use a fresh artifact directory per run, for example:

```text
artifacts/saleae/20260316-153000-sensor-rate/
  capture.sal
  i2c_table.csv
  irq_table.csv
  metrics.json
  serial.log
  report.md
```

## Signal-selection guidance

### I2C
Capture at least:
- `SCL`
- `SDA`
- optional `IRQ` or `DRDY`
- optional `RESET`
- optional power or analog channel if electrical behavior matters

Good questions to answer:
- is the device addressed correctly?
- are there missing ACKs?
- is repeated-start behavior correct?
- is the sensor sampled at the intended cadence?
- do protocol anomalies line up with IRQs or resets?

### SPI
Capture at least:
- `CLK`
- `CS`
- `MOSI`
- `MISO`
- optional `IRQ`, `RESET`, or a frame-sync GPIO

Good questions to answer:
- is chip select framing correct?
- is the command or response sequence consistent?
- is burst spacing stable?
- do wrong bytes align with timing or reset events?

### UART or Async Serial
Capture at least:
- `TX`
- `RX`
- optional flow control, boot, or reset lines

Good questions to answer:
- is the baud configuration correct?
- do frame drops line up with reset or power events?
- is request-response latency stable?

### Mixed-signal and analog
Add analog when you need to explain digital behavior, not just observe it.

Useful analog channels:
- supply rail
- current-sense output
- analog sensor output
- DAC or reference voltage

Analog is strongest for offline waveform analysis and correlation. Keep the report explicit about what was inferred from analog vs decoded protocol.

## Rate and jitter analysis

### Pick the right event
For sample-rate metrics, one event must correspond to one real sample. Common choices:
- rising edge of a data-ready interrupt
- HLA frame called `sample`
- I2C register read that fetches the latest sample
- SPI burst end or chip-select release for each sample frame

### What to compute
At minimum:
- event count
- first and last timestamp
- interval min, mean, max
- achieved mean rate in Hz
- standard deviation of interval
- p95 and p99 interval
- peak-to-peak jitter

### Interpret the result
When the mean rate looks correct but jitter is high, search for:
- multi-modal timing clusters
- bursty traffic separated by idle gaps
- missed events due to filtering on the wrong decoded row
- IRQ lines that drift relative to bus activity
- firmware scheduling interactions or power events

## Repo integration pattern
For reusable workflows, keep the automation script next to other lab utilities in the repo. Good naming patterns:
- `tools/saleae/capture_sensor_rate.py`
- `scripts/saleae/boot_capture.py`
- `tools/debug/saleae_spi_fault.py`

Also commit a short usage example such as:

```bash
python3 tools/saleae/capture_sensor_rate.py --port 10430 --artifact-root artifacts/saleae
```

## Reliability rules
- make every channel index explicit in code
- make every analyzer setting explicit in code
- export before teardown
- close the capture after export
- keep long monitoring as repeated short captures, not one giant capture
- do not assume another engineer's open Logic 2 tab contains the right state

## Safe embedded-development defaults
- prefer existing repo build or flash commands over inventing new ones
- do not toggle reset or power rails unless the repo already treats that as safe and repeatable
- when in doubt, capture passively first and collect evidence before changing hardware state
