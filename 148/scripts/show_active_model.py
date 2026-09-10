from __future__ import annotations

import argparse
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Read the active production model version pointer.")
    parser.add_argument("--repo-root", default=str(Path(__file__).resolve().parents[2]), help="Repo root path")
    parser.add_argument("--environment", choices=["prod", "dev"], default="prod", help="Environment to inspect")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo = Path(args.repo_root).resolve()

    if args.environment == "prod":
        marker = repo / "148" / "registry" / "models" / "qwen2_5_vl" / "production" / "current_version.txt"
        if not marker.exists():
            raise FileNotFoundError(f"Production pointer file not found: {marker}")
        print(marker.read_text(encoding="utf-8").strip())
        return 0

    env_file = repo / "152" / "config" / "dev.env"
    if not env_file.exists():
        raise FileNotFoundError(f"Dev config file not found: {env_file}")

    for line in env_file.read_text(encoding="utf-8").splitlines():
        if line.startswith("MODEL_VERSION="):
            print(line.split("=", 1)[1].strip())
            return 0

    raise ValueError(f"MODEL_VERSION not found in {env_file}")


if __name__ == "__main__":
    raise SystemExit(main())
