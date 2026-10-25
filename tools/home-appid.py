#!/usr/bin/env python3
"""Cambia la app de inicio del sistema (db/appfw/home_appid), a la que vuelve la tele al cerrar las apps.

  python3 tools/home-appid.py            # solo muestra el valor actual
  python3 tools/home-appid.py set        # com.samsung.tv.csfs -> tu app (APP_ID)
  python3 tools/home-appid.py restore    # tu app (APP_ID) -> com.samsung.tv.csfs

Es distinto del botón Home (operation/main en .appsvc.db, que cambia set-home.sh).
Solo cambia si el valor actual es exactamente el esperado, y relee la clave para comprobarlo.
"""
import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "vendor/samsung-tv-root"))
from samsung_tv_root.archive_root import probe

KEY = "db/appfw/home_appid"
STOCK = "com.samsung.tv.csfs"
MINE = os.environ.get("APP_ID", "MiInicioTV.Home")
GET = f"vconftool get {KEY}"


def change(expected, target):
    # Todo en una orden: comprobar, escribir, releer. Si algo no cuadra, se intenta dejar el valor original.
    return (
        f"cur=$({GET} | sed 's/.*value = //; s/ (String)$//'); echo \"antes: $cur\"; "
        f"if [ \"$cur\" != '{expected}' ]; then echo 'valor inesperado: no se cambia nada'; exit 3; fi; "
        f"vconftool set -t string {KEY} '{target}' -f; "
        f"new=$({GET} | sed 's/.*value = //; s/ (String)$//'); echo \"después: $new\"; "
        f"if [ \"$new\" != '{target}' ]; then vconftool set -t string {KEY} '{expected}' -f; echo 'no se pudo cambiar; restaurado'; exit 4; fi; "
        "echo OK"
    )


def main():
    tv = os.environ.get("TV_IP") or sys.exit("falta TV_IP")
    mode = sys.argv[1] if len(sys.argv) > 1 else "show"
    cmd = {"show": GET, "set": change(STOCK, MINE), "restore": change(MINE, STOCK)}.get(mode)
    if not cmd:
        sys.exit(__doc__)
    report = asyncio.run(probe(tv, commands=(cmd,)))
    c = report["commands"][0]
    print((c["stdout"] + c["stderr"]).strip())
    if not report.get("system_files_unchanged") or not report.get("staging_cleaned"):
        print("(aviso: la sesión no pasó sus comprobaciones)")
    sys.exit(0 if c["exit_code"] == 0 else 1)


if __name__ == "__main__":
    main()
