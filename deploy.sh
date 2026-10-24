#!/bin/bash
# Compila, firma e instala Mi Inicio en la tele.
# Uso:  TV_IP=192.168.1.50 CERT_PROFILE=MiPerfil ./deploy.sh
set -euo pipefail
cd "$(dirname "$0")"
source tools/tv-env.sh
: "${CERT_PROFILE:?Indica tu perfil de certificados de Tizen Studio: CERT_PROFILE=MiPerfil}"
APP_ID="$(grep -o 'tizen:application id="[^"]*"' app/config.xml | cut -d'"' -f2)"
OUT="$PWD/.buildResult"
rm -rf "$OUT"
echo ">> Compilando…"
tizen build-web -out "$OUT" -- app >/dev/null
echo ">> Firmando con el perfil $CERT_PROFILE…"
tizen package -t wgt -s "$CERT_PROFILE" -- "$OUT" >/dev/null
WGT="$(ls "$OUT"/*.wgt | head -1)"; cp "$WGT" "$OUT/MiInicio.wgt"
echo ">> Instalando…"
# La instalación se cuelga si la conexión sdb se cae: límite de 90 s y un reintento tras reiniciar sdb
install(){ perl -e 'alarm 90; exec @ARGV' tizen install -n MiInicio.wgt -s "$TV_IP:26101" -- "$OUT" 2>&1 | grep -iE 'completed|successfully|fail'; }
if ! install; then
  echo ">> La instalación no respondió; reiniciando sdb y reintentando…"
  sdb kill-server >/dev/null 2>&1; sleep 1; sdb start-server >/dev/null 2>&1; sdb connect "$TV_IP:26101" >/dev/null
  install
fi
echo ">> Abriendo…"
tizen run -p "$APP_ID" -s "$TV_IP:26101" | grep -iE 'launched|fail'
