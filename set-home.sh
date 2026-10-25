#!/bin/bash
# AVANZADO. Hace que el botón Home del mando abra Mi Inicio y que, al salir de una app con VOLVER, la tele vuelva a
# Mi Inicio en vez de al inicio de Samsung (son dos ajustes distintos: operation/main y db/appfw/home_appid).
# Usa una sesión de root TEMPORAL (sin tocar firmware ni dejar servicios). Antes guarda una copia de seguridad.
# Uso:            TV_IP=192.168.1.50 bash set-home.sh
# Deshacer:       TV_IP=192.168.1.50 bash set-home.sh stock     (¡siempre antes de desinstalar Mi Inicio!)
set -euo pipefail
cd "$(dirname "$0")"
source tools/tv-env.sh
export APP_ID="$(grep -o 'tizen:application id="[^"]*"' app/config.xml | cut -d'"' -f2)"
[ -f tools/home-routing/out/HomeRouting.dll ] || bash tools/build-helpers.sh

if [ "${1:-custom}" = "stock" ]; then
  echo ">> Volviendo al inicio de Samsung al salir de las apps…"
  python3 tools/home-appid.py restore || true
  echo ">> Volviendo al Home de Samsung…"
  exec python3 tools/home-routing.py --set stock
fi
echo ">> 1/5 Comprobando la sesión de root (debe salir uid=0 y system_files_unchanged: true)…"
python3 tools/tv-root.py --command 'id'
if [ ! -f tv-home-backup.tgz ]; then
  echo ">> 2/5 Copia de seguridad de los ajustes de apps de la tele…"
  python3 tools/tv-root.py --command "$(cat tools/extras/backup-tv-state.sh)" >/dev/null
  python3 tools/fetch-backup.py tv-home-backup.tgz
else
  echo ">> 2/5 Ya hay copia de seguridad (tv-home-backup.tgz), no se repite."
fi
echo ">> 3/5 Home actual (debe ser com.samsung.tv.csfs):"
python3 tools/home-routing.py
echo ">> 4/5 Asignando el botón Home a $APP_ID…"
python3 tools/home-routing.py --set custom || echo "   (no se cambió: si ya estaba asignado a $APP_ID, no pasa nada)"
echo ">> 5/5 Al salir de las apps, volver a $APP_ID…"
python3 tools/home-appid.py set || echo "   (no se cambió: si ya estaba en $APP_ID, no pasa nada)"
echo ">> Hecho. Prueba HOME en el mando y sal de una app con VOLVER: debería aparecer Mi Inicio."
