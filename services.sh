#!/bin/bash
# AVANZADO. Segunda fase de la limpieza: para los servicios del sistema de anuncios y analítica.
#   status   ver estado (solo lectura)
#   apply    parar y enmascarar; crea los dos interruptores permanentes de Samsung
#            (agente de anuncios, PISA y canalysis quedan apagados para siempre)
#   reapply  tras un reinicio en frío: volver a parar los que no tienen interruptor
#            (reconocimiento de contenido, analítica de medios, sp-kpi, kpi-logging)
#   restore  deshacerlo todo y volver a arrancarlos
# Uso: TV_IP=192.168.1.50 bash services.sh status|apply|reapply|restore
set -euo pipefail
cd "$(dirname "$0")"
source tools/tv-env.sh
[ -f tools/vendor/samsung-tv-root/samsung_tv_root/payloads/common31/SamsungTvRootAgent.dll ] || bash tools/build-helpers.sh
UNITS="adagent-service.service canalysis-service.service pisa-service.service contents-recognition-service.service org.tizen.tv.sp-kpi.service kpi-logging.service media-analytics-service.service pisa-service.path pisa-service.socket org.tizen.tv.media.analytics.service.busname"
P=tools/extras/privacy
case "${1:-status}" in
  status)  CMD="for u in $UNITS; do printf '%-46s ' \$u; systemctl show \$u -p LoadState -p ActiveState | paste -sd ' ' -; done; ls /opt/usr/share/systemd/system/" ;;
  apply)   CMD="$(cat $P/services-apply.sh)" ;;
  reapply) CMD="$(cat $P/services-reapply-after-reboot.sh)" ;;
  restore) CMD="$(cat $P/services-restore.sh)" ;;
  *) sed -n 2,9p "$0"; exit 1 ;;
esac
python3 tools/tv-root.py --command "$CMD" | python3 -c "
import sys, json
t = sys.stdin.read(); i = t.find('{')
r = json.loads(t[i:]) if i >= 0 else None
if not r: print(t); sys.exit(1)
c = r['commands'][0]; print(c['stdout'].strip()); print(c['stderr'].strip()[-800:])
print('archivos del sistema intactos:', r.get('system_files_unchanged'))
sys.exit(0 if c['exit_code'] == 0 else 1)"
