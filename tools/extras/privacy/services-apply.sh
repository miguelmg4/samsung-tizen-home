#!/bin/sh
# Run through tools/tv-root.py after taking the backup in docs/2-set-as-home.md.
# Stops and runtime-masks ad, analytics and content-recognition units, and writes two
# persistent startup markers. Undo with services-restore.sh.
set -eu
units="adagent-service.service canalysis-service.service pisa-service.service contents-recognition-service.service org.tizen.tv.sp-kpi.service kpi-logging.service media-analytics-service.service pisa-service.path pisa-service.socket org.tizen.tv.media.analytics.service.busname"
markers="pisa-service canalysis-daemon"
for unit in $units; do
    test -f "/usr/lib/systemd/system/$unit"
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
systemctl mask --runtime --no-reload $units
# This firmware can finish a reload after systemctl's acknowledgement times out.
if ! systemctl daemon-reload; then
    for unit in $units; do
        test "$(systemctl show "$unit" -p LoadState)" = LoadState=masked
    done
fi
systemctl stop --no-block $units
# En esta tele las paradas pueden tardar un poco más
sleep 3
for marker in $markers; do
    path="/opt/usr/share/systemd/system/$marker"
    if test ! -e "$path"; then
        (set -C; echo 'tv-home privacy 2026-10-20' >"$path")
        chmod 644 "$path"
    fi
done
for unit in $units; do
    test "$(readlink "/run/systemd/system/$unit")" = /dev/null
    state=$(systemctl show "$unit" -p ActiveState)
    test "$state" = ActiveState=inactive || test "$state" = ActiveState=failed
    case "$unit" in
        *.service) test "$(systemctl show "$unit" -p MainPID)" = MainPID=0 ;;
    esac
done
for marker in $markers; do
    test "$(cat "/opt/usr/share/systemd/system/$marker")" = 'tv-home privacy 2026-10-20'
done
echo 'Verified: all selected units stopped and masked; both persistent markers present.'
