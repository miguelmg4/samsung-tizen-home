#!/bin/sh
# Run through tools/tv-root.py. Undoes services-apply.sh: removes only its markers and masks,
# refusing to remove any file that has changed, then starts the services again.
set -eu
units="adagent-service.service canalysis-service.service pisa-service.service contents-recognition-service.service org.tizen.tv.sp-kpi.service kpi-logging.service media-analytics-service.service pisa-service.path pisa-service.socket org.tizen.tv.media.analytics.service.busname"
markers="pisa-service canalysis-daemon"
for unit in $units; do
    path="/run/systemd/system/$unit"
    if test -e "$path" || test -L "$path"; then
        test "$(readlink "$path")" = /dev/null
    fi
done
for marker in $markers; do
    path="/opt/usr/share/systemd/system/$marker"
    if test -e "$path" || test -L "$path"; then
        test ! -L "$path"
        test "$(cat "$path")" = 'tv-home privacy 2026-10-20'
    fi
done
for unit in $units; do
    rm -f "/run/systemd/system/$unit"
done
for marker in $markers; do
    rm -f "/opt/usr/share/systemd/system/$marker"
done
if ! systemctl daemon-reload; then
    for unit in $units; do
        test "$(systemctl show "$unit" -p LoadState)" = LoadState=loaded
    done
fi
# The socket was inactive and media-analytics was already failed before changes.
systemctl start adagent-service.service canalysis-service.service pisa-service.service contents-recognition-service.service org.tizen.tv.sp-kpi.service kpi-logging.service pisa-service.path org.tizen.tv.media.analytics.service.busname
for unit in $units; do
    test ! -e "/run/systemd/system/$unit"
    test ! -L "/run/systemd/system/$unit"
done
for marker in $markers; do
    test ! -e "/opt/usr/share/systemd/system/$marker"
done
echo 'Original service startup configuration restored.'
