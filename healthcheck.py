import sys
import urllib.request
import time

TARGET = "http://127.0.0.1:8000/health"
TIMEOUT = 10
RETRIES = 30


def main():
    for attempt in range(1, RETRIES + 1):
        try:
            with urllib.request.urlopen(TARGET, timeout=TIMEOUT) as resp:
                body = resp.read().decode("utf-8", errors="replace")
                print(f"Health-check success: HTTP {resp.status} -> {body}")
                return 0
        except Exception as exc:
            print(f"Attempt {attempt}/{RETRIES}: {exc}")
            time.sleep(2)

    print(f"Health-check failed: could not reach {TARGET} after {RETRIES} attempts.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
