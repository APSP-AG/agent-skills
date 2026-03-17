#!/usr/bin/env python3
"""Detect a local Logic 2 install, automation port availability, and repo context."""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import socket
import subprocess
from pathlib import Path
from typing import Iterable


PATH_CANDIDATES = [
    "Logic",
    "Logic.exe",
    "Logic2",
    "Logic2.exe",
]


def common_logic2_paths() -> list[Path]:
    system = platform.system()
    home = Path.home()
    paths: list[Path] = []

    env_path = os.environ.get("LOGIC2_PATH")
    if env_path:
        paths.append(Path(env_path))

    if system == "Darwin":
        paths.extend(
            [
                Path("/Applications/Logic 2.app/Contents/MacOS/Logic 2"),
                Path("/Applications/Logic.app/Contents/MacOS/Logic"),
            ]
        )
    elif system == "Windows":
        local_app_data = Path(os.environ.get("LOCALAPPDATA", ""))
        program_files = Path(os.environ.get("ProgramFiles", "C:/Program Files"))
        paths.extend(
            [
                local_app_data / "Programs" / "Logic" / "Logic.exe",
                program_files / "Saleae LLC" / "Logic" / "Logic.exe",
                program_files / "Logic" / "Logic.exe",
            ]
        )
    else:
        paths.extend(
            [
                Path("/usr/bin/Logic"),
                Path("/usr/local/bin/Logic"),
                home / ".local" / "bin" / "Logic",
                home / "Applications" / "Logic" / "Logic",
                home / "Applications" / "Logic 2" / "Logic 2",
            ]
        )

    deduped: list[Path] = []
    seen: set[str] = set()
    for path in paths:
        key = str(path)
        if key not in seen:
            deduped.append(path)
            seen.add(key)
    return deduped


def find_logic2() -> tuple[str | None, list[str]]:
    checked: list[str] = []
    for name in PATH_CANDIDATES:
        found = shutil.which(name)
        checked.append(f"PATH:{name}")
        if found:
            return found, checked

    for path in common_logic2_paths():
        checked.append(str(path))
        if path.exists():
            return str(path), checked

    return None, checked


def git_root(cwd: Path) -> str | None:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=str(cwd),
            check=True,
            capture_output=True,
            text=True,
        )
    except Exception:
        return None
    return completed.stdout.strip() or None


def port_open(host: str, port: int, timeout: float) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def automation_python_package() -> tuple[bool, str | None]:
    try:
        from saleae import automation  # noqa: F401
        return True, None
    except Exception as exc:
        return False, str(exc)


def launch_hints(executable: str | None) -> list[str]:
    if not executable:
        return [
            "Launch Logic 2 with automation enabled. Examples: Logic --automation or Logic.exe --automation",
            "If the automation port is non-default, include --automationPort <PORT>",
        ]

    return [
        f'"{executable}" --automation',
        f'"{executable}" --automation --automationPort 10430',
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1", help="Automation host to probe")
    parser.add_argument("--port", type=int, default=10430, help="Automation port to probe")
    parser.add_argument(
        "--timeout",
        type=float,
        default=0.5,
        help="Socket timeout in seconds when probing the automation port",
    )
    args = parser.parse_args()

    cwd = Path.cwd()
    logic_path, checked = find_logic2()

    package_available, package_error = automation_python_package()

    report = {
        "platform": platform.platform(),
        "python": platform.python_version(),
        "logic2_automation_python_package": {
            "available": package_available,
            "import_error": package_error,
            "install_hint": "pip install logic2-automation",
        },
        "cwd": str(cwd),
        "git_root": git_root(cwd),
        "logic2": {
            "found": logic_path is not None,
            "path": logic_path,
            "checked": checked,
            "automation_host": args.host,
            "automation_port": args.port,
            "automation_port_open": port_open(args.host, args.port, args.timeout),
            "launch_hints": launch_hints(logic_path),
        },
    }

    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
