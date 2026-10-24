#!/bin/bash
# Compila los ayudantes .NET que se ejecutan en la tele (solo para set-home.sh y debloat.sh).
# Necesita el SDK de .NET 6 (https://dotnet.microsoft.com/download/dotnet/6.0 o dotnet-install.sh --channel 6.0).
# Las teles de 2021-2022 traen .NET Core 3.1 y las de 2023+ .NET 6: se compila para las dos.
set -euo pipefail
TOOLS="$(cd "$(dirname "$0")" && pwd)"
VENDOR="$TOOLS/vendor/samsung-tv-root"
PAYLOADS="$VENDOR/samsung_tv_root/payloads"
export PATH="$HOME/.dotnet:$PATH" DOTNET_CLI_TELEMETRY_OPTOUT=1 DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=1
command -v dotnet >/dev/null || { echo "Falta el SDK de .NET 6 (dotnet)." >&2; exit 1; }
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT

build(){ # nombre carpeta-fuente framework salida
  local name=$1 src=$2 tfm=$3 out=$4
  local dir="$TMP/$name-$tfm"
  mkdir -p "$dir"; cp "$src"/*.cs "$dir/"
  sed "s#<TargetFramework>[^<]*</TargetFramework>#<TargetFramework>$tfm</TargetFramework>#" "$src/$name.csproj" > "$dir/$name.csproj"
  dotnet build "$dir/$name.csproj" --configuration Release --output "$out" -nologo -v q
}
for p in SamsungTvArchiveRoot SamsungTvRootAgent; do
  build $p "$VENDOR/payload-source" net6.0 "$PAYLOADS/common"
  build $p "$VENDOR/payload-source" netcoreapp3.1 "$PAYLOADS/common31"
done
dotnet build "$TOOLS/home-routing/HomeRouting.csproj" --configuration Release --output "$TOOLS/home-routing/out" -nologo -v q
echo "Ayudantes compilados."
