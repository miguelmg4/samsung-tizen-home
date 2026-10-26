#!/bin/bash
# AVANZADO. Ajustes rápidos: Multi View sin precarga al arrancar y limpieza de paquetes sobrantes.
# Uso: TV_IP=192.168.1.50 bash quickwins.sh check|apply|restore|clean
set -euo pipefail
cd "$(dirname "$0")"
source tools/tv-env.sh
[ -f tools/vendor/samsung-tv-root/samsung_tv_root/payloads/common31/SamsungTvRootAgent.dll ] || bash tools/build-helpers.sh
python3 tools/quickwins.py "${1:-check}"
