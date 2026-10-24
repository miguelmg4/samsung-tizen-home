# Configuración común de los scripts (se incluye con "source"). Necesita TV_IP.
: "${TV_IP:?Indica la IP de tu tele, p. ej.: TV_IP=192.168.1.50 bash $0}"
export TV_IP PATH="$HOME/tizen-studio/tools:$HOME/tizen-studio/tools/ide/bin:$HOME/.dotnet:$PATH"
command -v sdb >/dev/null || { echo "No encuentro sdb: instala Tizen Studio en ~/tizen-studio" >&2; exit 1; }
# La conexión sdb con la tele se cae a menudo: si no aparece en la lista, se reinicia el servidor sdb
sdb connect "$TV_IP:26101" >/dev/null 2>&1 || true
if ! sdb devices | grep -q "$TV_IP:26101"; then
  sdb kill-server >/dev/null 2>&1; sleep 1; sdb start-server >/dev/null 2>&1
  sdb connect "$TV_IP:26101" >/dev/null 2>&1 || true
  sdb devices | grep -q "$TV_IP:26101" || { echo "No se puede conectar con la tele ($TV_IP). ¿Está encendida, con el modo desarrollador y la IP de este ordenador como Host PC IP?" >&2; exit 1; }
fi
