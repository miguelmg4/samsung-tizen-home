#!/usr/bin/env python3
"""Run bounded commands through a temporary, authenticated TV root session."""
import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "vendor/samsung-tv-root"))
from samsung_tv_root.archive_root import probe


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tv", default=os.environ.get("TV_IP"), help="TV IP address (default: $TV_IP)")
    parser.add_argument("--command", action="append", required=True)
    args = parser.parse_args()
    if not args.tv:
        parser.error("pass --tv <ip> or set TV_IP")
    try:
        report = asyncio.run(probe(args.tv, commands=tuple(args.command)))
    except Exception as error:
        print(str(error), file=sys.stderr)
        return 1
    print(json.dumps(report, indent=2))
    return int(any(c["exit_code"] != 0 or c["timed_out"] for c in report["commands"]))


if __name__ == "__main__":
    sys.exit(main())
