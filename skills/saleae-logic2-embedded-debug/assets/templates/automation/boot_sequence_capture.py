#!/usr/bin/env python3
"""Starter workflow for boot-sequence capture around reset and first bus activity."""

from __future__ import annotations

from pathlib import Path

from saleae import automation


ARTIFACT_DIR = Path("artifacts/saleae/TODO-boot-sequence")
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

# TODO: patch these for the real bench setup.
DIGITAL_CHANNELS = [0, 1, 2, 3, 4]
CLK = 0
CS = 1
MOSI = 2
MISO = 3
RESET = 4
DIGITAL_SAMPLE_RATE = 25_000_000
CAPTURE_SECONDS = 2.0

SPI_ANALYZER_SETTINGS = {
    "MISO": MISO,
    "MOSI": MOSI,
    "Enable": CS,
    "Clock": CLK,
}


def main() -> int:
    with automation.Manager.connect(port=10430) as manager:
        device_configuration = automation.LogicDeviceConfiguration(
            enabled_digital_channels=DIGITAL_CHANNELS,
            digital_sample_rate=DIGITAL_SAMPLE_RATE,
        )
        capture_configuration = automation.CaptureConfiguration(
            capture_mode=automation.TimedCaptureMode(duration_seconds=CAPTURE_SECONDS)
        )

        # TODO: if the repo has a safe reset or flash command, run it immediately before or during the capture.
        capture = manager.start_capture(
            device_id=None,
            device_configuration=device_configuration,
            capture_configuration=capture_configuration,
        )
        capture.wait()

        spi = capture.add_analyzer("SPI", label="boot-spi", settings=SPI_ANALYZER_SETTINGS)
        capture.export_data_table(filepath=str(ARTIFACT_DIR / "spi_table.csv"), analyzers=[spi])
        capture.save_capture(filepath=str(ARTIFACT_DIR / "capture.sal"))
        capture.close()

    print("Boot capture complete. Diff the decoded transactions against a known-good sequence.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
