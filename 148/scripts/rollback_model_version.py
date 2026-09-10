from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().with_name("manage_model_version.py")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Roll back the prod model to a previously approved version.")
    parser.add_argument("--version", required=True, help="Version folder name to roll back to, e.g. v1_0_0")
    parser.add_argument("--dry-run", action="store_true", help="Print actions without writing files")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    command = [
        sys.executable,
        str(SCRIPT_PATH),
        "--version",
        args.version,
        "--environment",
        "prod",
    ]
    if args.dry_run:
        command.append("--dry-run")

    result = subprocess.run(command, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout.strip())
    if result.stderr:
        print(result.stderr.strip(), file=sys.stderr)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
