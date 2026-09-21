#!/usr/bin/env python3
from __future__ import annotations

import argparse


def main() -> None:
    parser = argparse.ArgumentParser(description="Print per-instance PX4 classroom MAVLink commands")
    parser.add_argument("--slots", type=int, default=12)
    parser.add_argument("--local-base", type=int, default=15600)
    parser.add_argument("--remote-base", type=int, default=14600)
    parser.add_argument("--rate", type=int, default=4_000_000)
    args = parser.parse_args()
    for instance in range(args.slots):
        local_port = args.local_base + instance
        remote_port = args.remote_base + instance
        print(
            f"# instance {instance} / slot {instance + 1}\n"
            f"mavlink start -u {local_port} -o {remote_port} -t 127.0.0.1 "
            f"-m onboard -r {args.rate}\n"
        )


if __name__ == "__main__":
    main()
