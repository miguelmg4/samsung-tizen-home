Source: https://github.com/chris-ritsen/samsung-tv-root
Commit: 4ad2c4d3b0d0e0da4b5b7ebe4a787e94596f416b
License: Unlicense (LICENSE).

Only the archive-root command channel and its direct dependencies are included.
Local change: tizen-runtime.patch supports the observed TU50DU7105KXXC custom dotnet host without --list-runtimes; it validates the resolved runtime path and checks libcoreclr.so exists.

The two payload DLLs are not committed; build them from the included sources with tools/build-helpers.sh (originally built with .NET SDK 6.0.428, net6.0, Release). No kernel exploit, firmware-flashing tool, persistent service, or UEP-disable payload is included.

Rebuild each payload-source/*.csproj with dotnet build --configuration Release --output samsung_tv_root/payloads/common.
Test: PYTHONPATH=. python3 test_tizen_runtime.py
