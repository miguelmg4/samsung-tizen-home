#!/usr/bin/env python3
"""Ajustes rápidos tomados de vetro (andrearicci93/vetro), por la sesión de root.

  python3 tools/quickwins.py check     # solo lectura: precarga de Multi View y paquetes sobrantes
  python3 tools/quickwins.py apply     # Multi View sin precarga al arrancar (~70 MB) y lo para ahora
  python3 tools/quickwins.py restore   # vuelve a precargar Multi View en el próximo arranque
  python3 tools/quickwins.py clean     # borra los .wgt/.tpk/.rpm que deja cada instalación

Multi View: la unidad de Samsung (multi-user.target) tiene ConditionPathExists=! sobre
.../data/disable_preloading; con ese archivo no se precarga y se abre en frío cuando se pide.
Paquetes: la tele copia cada paquete a sdk_tools/tmp antes de instalarlo y nunca lo borra.
"""
import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "vendor/samsung-tv-root"))
from samsung_tv_root.archive_root import probe

MS_ID = "com.samsung.tv.multiscreen"
MS_FLAG = "/home/owner/apps_rw/com.samsung.tv.multiscreen/data/disable_preloading"
STAGING = "/home/owner/share/tmp/sdk_tools/tmp"


def listed(app):
    return f"app_launcher -S 2>/dev/null | grep -q '^[[:space:]]*{app}[[:space:]]'"


CHECK = (
    f"[ -e {MS_FLAG} ] && echo 'Multi View: sin precarga' || echo 'Multi View: se precarga al arrancar'\n"
    f"{listed(MS_ID)} && echo 'Multi View: en marcha' || echo 'Multi View: parado'\n"
    f"echo 'Paquetes sobrantes:'; ls -la {STAGING} 2>/dev/null | grep -iE '\\.(wgt|tpk|rpm)$' || echo '  ninguno'\n"
    "df -h /opt | awk 'NR==2{print \"/opt: \"$5\" usado, \"$4\" libres\"}'"
)
APPLY = (
    "set -e\n"
    f"touch {MS_FLAG}\nchown owner:system_share {MS_FLAG}\nchmod 664 {MS_FLAG}\n"
    f"if {listed(MS_ID)}; then app_launcher -t {MS_ID} || true; fi\n"
    f"i=0; while {listed(MS_ID)} && [ $i -lt 10 ]; do sleep 0.5; i=$((i+1)); done\n"
    f"test -e {MS_FLAG} && echo 'OK Multi View sin precarga'"
)
RESTORE = f"rm -f {MS_FLAG} && echo 'OK Multi View vuelve a precargarse en el próximo arranque'"
# Solo archivos sueltos de paquete en la carpeta de instalación, uno a uno; nunca subcarpetas
CLEAN = (
    "b=$(df -kP /opt | awk 'NR==2{print $4}')\n"
    f"for f in {STAGING}/*; do\n"
    "  [ -f \"$f\" ] || continue\n"
    "  case \"$f\" in *.[wW][gG][tT]|*.[tT][pP][kK]|*.[rR][pP][mM]) rm -f \"$f\" && echo \"borrado ${f##*/}\";; esac\n"
    "done\n"
    "a=$(df -kP /opt | awk 'NR==2{print $4}')\n"
    "echo \"liberados $(( (a - b) / 1024 )) MB en /opt\""
)


def run(tv, cmd):
    report = asyncio.run(probe(tv, commands=(cmd,)))
    if not report.get("system_files_unchanged") or not report.get("staging_cleaned"):
        raise RuntimeError("la sesión de root no pasó sus comprobaciones")
    c = report["commands"][0]
    if c["exit_code"] != 0 or c["timed_out"]:
        raise RuntimeError("falló:\n" + c["stdout"] + c["stderr"])
    return c["stdout"].strip()


def main():
    tv = os.environ.get("TV_IP") or sys.exit("falta TV_IP")
    mode = sys.argv[1] if len(sys.argv) > 1 else "check"
    cmd = {"check": CHECK, "apply": APPLY, "restore": RESTORE, "clean": CLEAN}.get(mode)
    if not cmd:
        sys.exit(__doc__)
    print(run(tv, cmd))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
