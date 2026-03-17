#!/usr/bin/env python3
"""Starter workflow for I2C sample-rate and jitter captures with Saleae Logic 2."""

from __future__ import annotations

from pathlib import Path

from saleae import automation


ARTIFACT_DIR = Path("artifacts/saleae/TODO-i2c-rate")
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

# TODO: fill in the real channel mapping from the repo and bench setup.
DIGITAL_CHANNELS = [0, 1, 2]
ANALOG_CHANNELS = []
SCL_CHANNEL = 0
SDA_CHANNEL = 1
IRQ_CHANNEL = 2  # optional, remove if unused

DIGITAL_SAMPLE_RATE = 10_000_000
ANALOG_SAMPLE_RATE = None
CAPTURE_SECONDS = 5.0

# TODO: add the real analyzer settings required by your device and wiring.
I2C_ANALYZER_SETTINGS = {
    "SCL": SCL_CHANNEL,
    "SDA": SDA_CHANNEL,
}


def main() -> int:
    # Update this if Logic 2 is listening on a non-default port.
    with automation.Manager.connect(port=10430) as manager:
        device_configuration = automation.LogicDeviceConfiguration(
            enabled_digital_channels=DIGITAL_CHANNELS,
            digital_sample_rate=DIGITAL_SAMPLE_RATE,
            enabled_analog_channels=ANALOG_CHANNELS,
            analog_sample_rate=ANALOG_SAMPLE_RATE,
        )
        capture_configuration = automation.CaptureConfiguration(
            capture_mode=automation.TimedCaptureMode(duration_seconds=CAPTURE_SECONDS)
        )

        capture = manager.start_capture(
            device_id=None,
            device_configuration=device_configuration,
            capture_configuration=capture_configuration,
        )

        capture.wait()

        i2c = capture.add_analyzer("I2C", label="sensor-bus", settings=I2C_ANALYZER_SETTINGS)

        table_path = ARTIFACT_DIR / "i2c_table.csv"
        capture.export_data_table(filepath=str(table_path), analyzers=[i2c])

        # Optional but helpful for replay in the UI.
        capture.save_capture(filepath=str(ARTIFACT_DIR / "capture.sal"))
        capture.close()

    print(f"Wrote {table_path}")
    print("Next step: filter rows that represent one real sample, then run saleae_interval_metrics.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
