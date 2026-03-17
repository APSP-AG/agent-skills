# Embedded debug recipes

## Sensor sampling rate over I2C
Goal: prove actual achieved sample rate and jitter, not just configured rate.

Recommended workflow:
1. search the repo for the sensor address, sample register, data-ready interrupt, nominal ODR, and any batching behavior
2. capture `SCL`, `SDA`, and `DRDY` or `IRQ` if available
3. add the built-in I2C analyzer
4. if the bus traffic is noisy, add an HLA that emits one semantic `sample` frame per sensor read
5. export the data table
6. compute interval stats using `scripts/saleae_interval_metrics.py`
7. compare bus-based timing vs IRQ-based timing if both are available

Best artifact set:
- decoded I2C CSV
- IRQ or GPIO timestamp CSV if captured
- metrics JSON
- short Markdown report with assumptions and selected event definition

## Boot handshake failure on SPI
Goal: determine why an early boot transaction fails.

Recommended workflow:
1. diff recent commits in the transport, bootloader, and board-init paths
2. capture `CLK`, `CS`, `MOSI`, `MISO`, and `RESET`
3. start with a timed capture that spans reset through first response
4. export decoded SPI transactions and save `.sal` for replay
5. if command bytes are known, build an HLA that labels each command and response pair
6. highlight first deviation from a known-good boot sequence

Best artifact set:
- `boot_sequence_capture.py`
- decoded SPI CSV
- optional HLA extension folder
- report showing first mismatching transaction

## Interrupt latency correlation
Goal: determine whether firmware or hardware introduces latency between an IRQ edge and bus servicing.

Recommended workflow:
1. capture IRQ line plus the serviced bus lines
2. export timestamps for the IRQ event and the first matching service transaction
3. compute latency per event in a small repo-side analysis script
4. report median, worst-case, and tail latency

Good follow-ups:
- correlate with RTOS tick or logging output
- compare before and after a firmware scheduling change

## Power or analog correlation
Goal: explain digital or protocol anomalies using analog evidence.

Recommended workflow:
1. capture the bus or control lines plus one analog rail or analog sensor output
2. keep the question specific: reset event, rail droop, overshoot, or settling window
3. export decoded protocol plus analog raw data
4. align the timelines in the report and make the causal claim explicit only when the evidence supports it

Good report phrasing:
- `the missing ack occurs within the same window as the 3.3 V rail dip`
- `sample timing widens after the analog front-end takes longer to settle`

## Regression capture for GitHub PRs
Goal: turn a flaky or protocol-sensitive behavior into a repeatable hardware regression.

Recommended workflow:
1. identify a single firmware action that reproduces the bug
2. codify build, flash, run, capture, and export steps in one script
3. store artifacts under a fresh timestamped directory
4. emit a machine-readable summary or exit code for CI
5. attach the short Markdown report and artifact paths to the PR or job log

Keep the automated workflow narrow. One focused scenario is better than a giant do-everything bench script.
