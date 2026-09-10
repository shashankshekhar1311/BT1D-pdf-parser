from __future__ import annotations

import argparse
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Promote or roll back a model version in the registry and update the relevant env files."
    )
    parser.add_argument("--version", required=True, help="Model version folder name, e.g. v1_0_0 or v1_1_0_dev")
    parser.add_argument("--environment", choices=["prod", "dev"], required=True, help="Environment to target")
    parser.add_argument("--repo-root", default=str(Path(__file__).resolve().parents[2]), help="Repo root path")
    parser.add_argument("--dry-run", action="store_true", help="Print the actions without writing files")
    return parser.parse_args()


def repo_path(repo_root: str) -> Path:
    return Path(repo_root).resolve()


def registry_root(repo_root: Path) -> Path:
    return repo_root / "148" / "registry" / "models" / "qwen2_5_vl"


def current_prod_pointer(registry: Path) -> Path:
    return registry / "production" / "current_version.txt"


def ensure_version_exists(registry: Path, version: str) -> Path:
    version_dir = registry / version
    if not version_dir.exists():
        raise FileNotFoundError(f"Model version directory not found: {version_dir}")
    if not (version_dir / "metadata.json").exists():
        raise FileNotFoundError(f"Missing metadata.json for version {version} in {version_dir}")
    return version_dir


def update_file_key(file_path: Path, key: str, value: str) -> None:
    original_lines = file_path.read_text(encoding="utf-8").splitlines()
    new_lines: list[str] = []
    seen = False

    for line in original_lines:
        stripped = line.strip()
        if stripped.startswith("#"):
            new_lines.append(line)
            continue
        if "=" in line and not stripped.startswith("#"):
            current_key, _, _ = line.partition("=")
            if current_key == key:
                new_lines.append(f"{key}={value}")
                seen = True
                continue
        new_lines.append(line)

    if not seen:
        new_lines.append(f"{key}={value}")

    file_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")


def apply_environment_updates(repo_root: Path, environment: str, version: str) -> None:
    model_root = registry_root(repo_root)
    version_dir = model_root / version
    version_path = str(version_dir).replace("\\", "/")

    if environment == "prod":
        env_files = [
            repo_root / "148" / "config" / "prod_model.env",
            repo_root / "152" / "config" / "prod.env",
        ]
        pointer_file = current_prod_pointer(model_root)
        update_file_key(pointer_file, "CURRENT_VERSION", version)
    else:
        env_files = [
            repo_root / "148" / "config" / "dev.env",
            repo_root / "152" / "config" / "dev.env",
        ]
        pointer_file = None

    for env_file in env_files:
        if not env_file.exists():
            raise FileNotFoundError(f"Environment file not found: {env_file}")
        update_file_key(env_file, "MODEL_VERSION", version)
        update_file_key(env_file, "MODEL_PATH", version_path)

    if pointer_file is not None and pointer_file.exists():
        pointer_file.write_text(version + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    root = repo_path(args.repo_root)
    registry = registry_root(root)

    try:
        ensure_version_exists(registry, args.version)
    except FileNotFoundError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1

    print(f"[MODEL] Validated version: {args.version}")
    print(f"[MODEL] Registry root: {registry}")
    print(f"[MODEL] Environment target: {args.environment}")

    if args.dry_run:
        print("[DRY RUN] No files written.")
        return 0

    try:
        apply_environment_updates(root, args.environment, args.version)
    except FileNotFoundError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1

    print(f"[OK] Updated env files for {args.environment} to use model version {args.version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
