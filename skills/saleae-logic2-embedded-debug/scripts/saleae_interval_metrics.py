#!/usr/bin/env python3
"""Compute interval, rate, and jitter statistics from a timestamp CSV export."""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import statistics
from datetime import datetime
from pathlib import Path
from typing import Iterable


def parse_time(value: str) -> tuple[float, str]:
    text = value.strip()
    try:
        return float(text), "numeric"
    except ValueError:
        pass

    iso_text = text.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(iso_text).timestamp(), "iso8601"
    except ValueError as exc:
        raise ValueError(f"Cannot parse timestamp value: {value!r}") from exc


def percentile(sorted_values: list[float], pct: float) -> float:
    if not sorted_values:
        raise ValueError("Cannot compute a percentile of an empty list")
    if len(sorted_values) == 1:
        return sorted_values[0]
    position = (len(sorted_values) - 1) * pct
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return sorted_values[lower]
    fraction = position - lower
    return sorted_values[lower] + (sorted_values[upper] - sorted_values[lower]) * fraction


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", required=True, dest="csv_path", help="Input CSV file")
    parser.add_argument("--time-column", required=True, help="Column containing timestamps")
    parser.add_argument("--match-column", help="Optional column to regex-filter")
    parser.add_argument("--match-regex", help="Regex used with --match-column or against the whole row")
    parser.add_argument(
        "--time-scale",
        type=float,
        default=1.0,
        help="Scale applied to numeric timestamps to convert them to seconds",
    )
    parser.add_argument("--output", help="Optional path to write JSON results")
    args = parser.parse_args()

    csv_path = Path(args.csv_path)
    if not csv_path.exists():
        raise SystemExit(f"CSV file not found: {csv_path}")

    regex = re.compile(args.match_regex) if args.match_regex else None
    timestamps: list[float] = []
    parse_mode = None

    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if args.time_column not in (reader.fieldnames or []):
            raise SystemExit(
                f"Time column {args.time_column!r} not found. Available columns: {reader.fieldnames}"
            )

        for row in reader:
            if regex:
                if args.match_column:
                    candidate = row.get(args.match_column, "")
                else:
                    candidate = " ".join((value or "") for value in row.values())
                if not regex.search(candidate):
                    continue

            raw_value = row.get(args.time_column, "")
            if raw_value is None or not str(raw_value).strip():
                continue

            parsed, mode = parse_time(str(raw_value))
            parse_mode = parse_mode or mode
            if mode == "numeric":
                parsed *= args.time_scale
            timestamps.append(parsed)

    if len(timestamps) < 2:
        raise SystemExit("Need at least two matching timestamps to compute intervals")

    intervals = [later - earlier for earlier, later in zip(timestamps, timestamps[1:])]
    sorted_intervals = sorted(intervals)
    mean_interval = statistics.fmean(intervals)
    stdev_interval = statistics.pstdev(intervals) if len(intervals) > 1 else 0.0
    mean_rate_hz = 1.0 / mean_interval if mean_interval > 0 else math.inf

    payload = {
        "source_csv": str(csv_path.resolve()),
        "time_column": args.time_column,
        "match_column": args.match_column,
        "match_regex": args.match_regex,
        "timestamp_parse_mode": parse_mode,
        "event_count": len(timestamps),
        "interval_count": len(intervals),
        "first_timestamp": timestamps[0],
        "last_timestamp": timestamps[-1],
        "stats": {
            "mean_interval_s": mean_interval,
            "median_interval_s": statistics.median(intervals),
            "min_interval_s": min(intervals),
            "max_interval_s": max(intervals),
            "stdev_interval_s": stdev_interval,
            "p95_interval_s": percentile(sorted_intervals, 0.95),
            "p99_interval_s": percentile(sorted_intervals, 0.99),
            "peak_to_peak_jitter_s": max(intervals) - min(intervals),
            "coefficient_of_variation": (stdev_interval / mean_interval) if mean_interval else None,
            "mean_rate_hz": mean_rate_hz,
        },
    }

    output = json.dumps(payload, indent=2, sort_keys=True)
    print(output)
    if args.output:
        Path(args.output).write_text(output + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
