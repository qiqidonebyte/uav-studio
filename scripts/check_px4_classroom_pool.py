#!/usr/bin/env python3
from __future__ import annotations

import argparse
import time

import httpx


def main() -> None:
    parser = argparse.ArgumentParser(description="Check UAV Studio classroom PX4 pool")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--username", default="admin")
    parser.add_argument("--password", required=True)
    parser.add_argument("--watch", action="store_true")
    args = parser.parse_args()

    with httpx.Client(base_url=args.base_url, timeout=10.0) as client:
        response = client.post("/api/auth/login", json={"username": args.username, "password": args.password})
        response.raise_for_status()
        while True:
            pool = client.get("/api/teacher/px4-pool")
            pool.raise_for_status()
            payload = pool.json()
            print(
                f"pool={payload['pool_size']} used={payload['used']} "
                f"free={payload['free']} queued={payload['queued']}"
            )
            for slot in payload.get("slots", []):
                if slot.get("run_id") is not None or slot.get("last_error"):
                    print(
                        f"  slot={slot['slot_id']:02d} port={slot['port']} "
                        f"run={slot.get('run_id')} connected={slot.get('connected')} "
                        f"error={slot.get('last_error') or '-'}"
                    )
            if not args.watch:
                break
            time.sleep(2)


if __name__ == "__main__":
    main()
