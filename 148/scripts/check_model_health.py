from __future__ import annotations

import argparse
import json
import sys
from urllib import error, request


PORTS = {
    "prod": {"model": 9000, "gateway": 8000},
    "dev": {"model": 9001, "gateway": 8001},
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check the health of the model and gateway endpoints for a given environment.")
    parser.add_argument("--environment", choices=["prod", "dev"], required=True, help="Environment to check")
    parser.add_argument("--host", default="127.0.0.1", help="Host to query")
    return parser.parse_args()


def fetch_json(url: str) -> dict:
    try:
        with request.urlopen(url, timeout=10) as resp:
            body = resp.read().decode("utf-8")
            payload = json.loads(body)
            return payload
    except error.URLError as exc:
        raise RuntimeError(f"Unable to reach {url}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Health endpoint returned invalid JSON at {url}: {exc}") from exc


def main() -> int:
    args = parse_args()
    ports = PORTS[args.environment]
    checked = []

    for label, port in ports.items():
        url = f"http://{args.host}:{port}/health"
        try:
            payload = fetch_json(url)
            status = payload.get("status") if isinstance(payload, dict) else None
            if status != "healthy":
                print(f"[FAIL] {label} health at {url} returned status={status!r}", file=sys.stderr)
                return 1
            print(f"[OK] {label} health at {url}: {payload}")
            checked.append(label)
        except RuntimeError as exc:
            print(f"[FAIL] {exc}", file=sys.stderr)
            return 1

    print(f"[OK] Environment {args.environment} health checks passed for: {', '.join(checked)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
