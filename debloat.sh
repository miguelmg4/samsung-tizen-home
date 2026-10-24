#!/bin/bash
# AVANZADO. Desactiva (no desinstala) anuncios, rastreo y extras de Samsung. Reversible con "restore".
# Uso: TV_IP=192.168.1.50 bash debloat.sh inspect|check|apply|restore [grupos]
#      grupos por defecto: ads,tracking,promo   (ver tools/debloat.py para la lista completa)
set -euo pipefail
cd "$(dirname "$0")"
source tools/tv-env.sh
[ -f tools/vendor/samsung-tv-root/samsung_tv_root/payloads/common31/SamsungTvRootAgent.dll ] || bash tools/build-helpers.sh
python3 tools/debloat.py "${1:-check}" ${2:+"$2"}
