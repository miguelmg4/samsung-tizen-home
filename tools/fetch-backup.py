#!/usr/bin/env python3
"""Descarga tv-home-backup.tgz por la sesión de root (este firmware no deja usar sdb pull en sdk_tools)."""
import asyncio
import base64
import hashlib
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "vendor/samsung-tv-root"))
from samsung_tv_root.archive_root import probe

REMOTE = "/home/owner/share/tmp/sdk_tools/tv-home-backup.tgz"
CHUNK = 600_000  # en base64 ocupa ~800 KB, por debajo del límite de 1 MiB por salida


def run(tv, commands):
    report = asyncio.run(probe(tv, commands=tuple(commands)))
    if not report.get("system_files_unchanged") or not report.get("staging_cleaned"):
        raise RuntimeError("la sesión de root no pasó sus comprobaciones")
    for c in report["commands"]:
        if c["exit_code"] != 0 or c["timed_out"]:
            raise RuntimeError("falló: " + c["command"] + "\n" + c["stderr"])
    return [c["stdout"] for c in report["commands"]]


def main():
    tv = os.environ.get("TV_IP") or sys.exit("falta TV_IP")
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "tv-home-backup.tgz")
    size_out, sum_out = run(tv, ["stat -c %s " + REMOTE, "sha256sum " + REMOTE])
    size, expected = int(size_out.strip()), sum_out.split()[0]
    parts = (size + CHUNK - 1) // CHUNK
    cmds = [f"dd if={REMOTE} bs={CHUNK} skip={i} count=1 2>/dev/null | base64" for i in range(parts)]
    data = b"".join(base64.b64decode("".join(s.split())) for s in run(tv, cmds))
    got = hashlib.sha256(data).hexdigest()
    if len(data) != size or got != expected:
        sys.exit(f"copia incompleta: {len(data)}/{size} bytes, sha256 {got} != {expected}")
    out.write_bytes(data)
    print(f"{out}: {size} bytes, sha256 {got} (coincide con la tele)")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
