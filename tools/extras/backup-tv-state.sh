#!/bin/sh
# Run through tools/tv-root.py before changing Home routing or privacy settings.
# Takes consistent SQLite snapshots of the app, Home-routing and notification databases
# plus the systemd override folders, and leaves one archive where sdb can pull it.
# This is a settings backup, not a firmware image.
set -eu
umask 077
out=/home/owner/share/tmp/sdk_tools
b=$out/tv-home-backup
mkdir "$b"
sqlite3 /opt/dbspace/.pkgmgr_parser.db ".backup $b/global-pkg.db"
sqlite3 /opt/dbspace/user/5001/.pkgmgr_parser.db ".backup $b/user-pkg.db"
sqlite3 /opt/dbspace/.notification.db ".backup $b/notification.db"
sqlite3 /opt/dbspace/.appsvc.db ".backup $b/global-appsvc.db"
sqlite3 /opt/dbspace/user/5001/.appsvc.db ".backup $b/user-appsvc.db"
sqlite3 /opt/dbspace/.app-context.db ".backup $b/app-context.db"
for db in $b/*.db; do test "$(sqlite3 "$db" 'PRAGMA integrity_check;')" = ok; done
cp -a /opt/usr/share/systemd/system $b/opt-systemd
cp -a /run/systemd/system $b/runtime-systemd
ps -eo pid,user,stat,args >$b/processes.txt
tar czf $out/tv-home-backup.tgz -C $b .
rm -rf "$b"
chmod 644 $out/tv-home-backup.tgz
sha256sum $out/tv-home-backup.tgz
