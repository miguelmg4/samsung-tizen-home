#!/bin/bash
# AVANZADO. Hace que el botón Home del mando abra Mi Inicio (y, con «Ejecutar Smart Hub», también al encender).
# Usa una sesión de root TEMPORAL (sin tocar firmware ni dejar servicios). Antes guarda una copia de seguridad.
# Uso:            TV_IP=192.168.1.50 bash set-home.sh
# Deshacer:       TV_IP=192.168.1.50 bash set-home.sh stock     (¡siempre antes de desinstalar Mi Inicio!)
set -euo pipefail
cd "$(dirname "$0")"
source tools/tv-env.sh
export APP_ID="$(grep -o 'tizen:application id="[^"]*"' app/config.xml | cut -d'"' -f2)"
[ -f tools/home-routing/out/HomeRouting.dll ] || bash tools/build-helpers.sh

if [ "${1:-custom}" = "stock" ]; then
  echo ">> Volviendo al Home de Samsung…"
  exec python3 tools/home-routing.py --set stock
fi
echo ">> 1/4 Comprobando la sesión de root (debe salir uid=0 y system_files_unchanged: true)…"
python3 tools/tv-root.py --command 'id'
if [ ! -f tv-home-backup.tgz ]; then
  echo ">> 2/4 Copia de seguridad de los ajustes de apps de la tele…"
  python3 tools/tv-root.py --command "$(cat tools/extras/backup-tv-state.sh)" >/dev/null
  python3 tools/fetch-backup.py tv-home-backup.tgz
else
  echo ">> 2/4 Ya hay copia de seguridad (tv-home-backup.tgz), no se repite."
fi
echo ">> 3/4 Home actual (debe ser com.samsung.tv.csfs):"
python3 tools/home-routing.py
echo ">> 4/4 Asignando el botón Home a $APP_ID…"
python3 tools/home-routing.py --set custom
echo ">> Hecho. Abre otra app y pulsa HOME en el mando."
