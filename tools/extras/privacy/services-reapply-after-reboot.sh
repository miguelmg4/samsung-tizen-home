#!/bin/sh
# Run through tools/tv-root.py. Re-applies the runtime masks from services-apply.sh,
# which a reboot clears. Undo with services-restore-runtime.sh.
set -eu
units="adagent-service.service canalysis-service.service pisa-service.service contents-recognition-service.service org.tizen.tv.sp-kpi.service kpi-logging.service media-analytics-service.service pisa-service.path pisa-service.socket org.tizen.tv.media.analytics.service.busname"
for u in $units; do test -f /usr/lib/systemd/system/$u; if test -e /run/systemd/system/$u || test -L /run/systemd/system/$u; then test "$(readlink /run/systemd/system/$u)" = /dev/null; fi; done
nsenter --target 1 --mount /bin/systemctl mask --runtime --no-reload $units
nsenter --target 1 --mount /bin/systemctl daemon-reload
nsenter --target 1 --mount /bin/systemctl stop --no-block $units
nsenter --target 1 --mount /bin/systemctl show $units -p Id -p LoadState -p ActiveState -p MainPID
