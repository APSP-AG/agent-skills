#!/usr/bin/env python3
"""Scaffold a Saleae Logic 2 HLA or measurement extension folder."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return slug or "saleae-extension"


def write(path: Path, content: str) -> None:
    path.write_text(content.strip() + "\n", encoding="utf-8")


def hla_python() -> str:
    return '''from saleae.analyzers import AnalyzerFrame, HighLevelAnalyzer


class Hla(HighLevelAnalyzer):
    """Replace this pass-through example with a repo-specific semantic decoder."""

    result_types = {
        "message": {
            "format": "{{data.summary}}",
        },
        "error": {
            "format": "ERR {{data.summary}}",
        },
    }

    def __init__(self):
        self._state = {}

    def decode(self, frame: AnalyzerFrame):
        # TODO:
        # 1. inspect frame.type and frame.data from the input analyzer
        # 2. accumulate state across frames when a semantic message spans multiple frames
        # 3. emit stable field names for export, not just a display string
        summary = f"{frame.type}: {frame.data}"
        return AnalyzerFrame("message", frame.start_time, frame.end_time, {"summary": summary})
'''


def measurement_python(kind: str, metric_key: str) -> str:
    base_class = "DigitalMeasurer" if kind == "digital-measurement" else "AnalogMeasurer"
    class_name = "DigitalMeasurement" if kind == "digital-measurement" else "AnalogMeasurement"
    process_hint = (
        "for t, bitstate in data:\n            # Note: the first item indicates the state at the start of the selected range.\n            pass"
        if kind == "digital-measurement"
        else "# data.samples is a numpy array. Accumulate state across chunks here.\n        pass"
    )

    return f'''from saleae.range_measurements import {base_class}


METRIC_KEY = "{metric_key}"


class {class_name}({base_class}):
    supported_measurements = [METRIC_KEY]

    def __init__(self, requested_measurements):
        super().__init__(requested_measurements)
        self.requested_measurements = requested_measurements
        self._count = 0

    def process_data(self, data):
        {process_hint}

    def measure(self):
        values = {{}}
        # TODO: replace the placeholder with a real measurement in canonical units.
        values[METRIC_KEY] = float(self._count)
        return values
'''


def extension_json(
    kind: str,
    display_name: str,
    author: str,
    description: str,
    metric_key: str,
    metric_name: str,
    metric_notation: str,
    metric_units: str,
) -> str:
    if kind == "hla":
        extensions = {
            display_name: {
                "type": "HighLevelAnalyzer",
                "entryPoint": "HighLevelAnalyzer.Hla",
            }
        }
    elif kind == "digital-measurement":
        extensions = {
            display_name: {
                "type": "DigitalMeasurement",
                "entryPoint": "DigitalMeasurement.DigitalMeasurement",
                "metrics": {
                    metric_key: {
                        "name": metric_name,
                        "notation": metric_notation,
                        "units": metric_units,
                    }
                },
            }
        }
    else:
        extensions = {
            display_name: {
                "type": "AnalogMeasurement",
                "entryPoint": "AnalogMeasurement.AnalogMeasurement",
                "metrics": {
                    metric_key: {
                        "name": metric_name,
                        "notation": metric_notation,
                        "units": metric_units,
                    }
                },
            }
        }

    payload = {
        "version": "0.0.1",
        "apiVersion": "1.0.0",
        "author": author,
        "description": description,
        "name": display_name,
        "extensions": extensions,
    }
    return json.dumps(payload, indent=2)


def readme(kind: str, display_name: str) -> str:
    extension_kind = {
        "hla": "High-Level Analyzer",
        "digital-measurement": "Digital Measurement",
        "analog-measurement": "Analog Measurement",
    }[kind]
    return f'''# {display_name}

## What this extension is
This is a scaffolded Saleae Logic 2 {extension_kind} extension.

## How to customize it
1. Patch `extension.json` to finalize names, metrics, and metadata.
2. Replace the placeholder logic in the generated Python file with repo-specific behavior.
3. Validate it against a known-good capture.
4. Load `extension.json` from Logic 2.

## Embedded-debug notes
- Use names from the firmware repo for registers, commands, states, and fields.
- Keep parsing or measurement math in helper functions that can be tested outside Logic 2.
- Favor stable exported field names so automation scripts can post-process the results.
'''


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--kind",
        required=True,
        choices=["hla", "digital-measurement", "analog-measurement"],
        help="Extension type to scaffold",
    )
    parser.add_argument("--display-name", required=True, help="Human-readable extension name")
    parser.add_argument("--output", required=True, help="Directory to create")
    parser.add_argument("--author", default="Your Team", help="Extension author")
    parser.add_argument(
        "--description",
        default="Scaffolded Saleae Logic 2 extension for embedded debugging",
        help="Extension description",
    )
    parser.add_argument("--metric-key", default="primaryMetric", help="Metric key for measurement extensions")
    parser.add_argument("--metric-name", default="Primary Metric", help="Metric label for measurement extensions")
    parser.add_argument("--metric-notation", default="M", help="Metric notation for measurement extensions")
    parser.add_argument("--metric-units", default="unit", help="Metric units for measurement extensions")
    args = parser.parse_args()

    output_dir = Path(args.output).resolve()
    if output_dir.exists() and any(output_dir.iterdir()):
        raise SystemExit(f"Output directory already exists and is not empty: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)

    write(
        output_dir / "extension.json",
        extension_json(
            args.kind,
            args.display_name,
            args.author,
            args.description,
            args.metric_key,
            args.metric_name,
            args.metric_notation,
            args.metric_units,
        ),
    )
    write(output_dir / "README.md", readme(args.kind, args.display_name))

    if args.kind == "hla":
        write(output_dir / "HighLevelAnalyzer.py", hla_python())
    elif args.kind == "digital-measurement":
        write(output_dir / "DigitalMeasurement.py", measurement_python(args.kind, args.metric_key))
    else:
        write(output_dir / "AnalogMeasurement.py", measurement_python(args.kind, args.metric_key))

    print(f"Created {args.kind} extension scaffold at {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
