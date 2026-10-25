#!/usr/bin/env python3
"""Desactiva (no desinstala) apps de anuncios, rastreo y extras de una tele Samsung, por la sesión de root.

  python3 tools/debloat.py inspect                 # solo lectura: qué procesos gastan más memoria
  python3 tools/debloat.py check  [grupos]         # solo lectura: qué existe y su estado
  python3 tools/debloat.py apply  [grupos]         # desactiva las de esos grupos que existan; guarda la lista
  python3 tools/debloat.py restore                 # reactiva exactamente lo que desactivó apply

Grupos (separados por comas). Por defecto: ads,tracking,promo
  ads, tracking, promo, alexa, health, smartthings, art, bixby, applevideo, samsunghome
Ejemplo: python3 tools/debloat.py apply ads,tracking,promo,alexa,smartthings

Usa `pkgcmd -D/-A --uid 5001`, la herramienta de paquetes de Tizen: persiste tras reiniciar y es reversible.
Basado en extras/privacy de berteotti/custom-tv (MIT). Probado en un modelo de 2022 con Tizen 6.5.
"""
import asyncio
import os
import shlex
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "vendor/samsung-tv-root"))
from samsung_tv_root.archive_root import probe

# grupo -> {id de app: motivo}. Las apps que no existan en tu modelo se saltan solas.
GROUPS = {
    "ads": {
        "adplatform.ADPlayer": "reproductor de anuncios",
        "com.samsung.tv.adplayer": "reproductor de anuncios",
        "com.samsung.tv.ad-web-framework": "anuncios web",
        "com.samsung.tv.coba.adagent": "agente de anuncios",
        "com.samsung.tv.adagent-service": "servicio de anuncios",
        "com.samsung.tv.targeted-ad-service": "anuncios personalizados",
    },
    "tracking": {
        "com.samsung.tv.acr": "reconoce lo que ves (ACR)",
        "com.samsung.tv.contents-recognition-dbmgr": "reconocimiento de contenido",
        "com.samsung.tv.canalysis-service": "analítica de uso",
        "com.samsung.tv.pisa-service": "analítica (PISA)",
        "org.tizen.pisa-control-service": "analítica (PISA)",
    },
    "promo": {
        "com.samsung.tv.bixby-promotion": "promoción de Bixby",
        "g0l3ad0res.emanual": "e-Manual",
        "J9fZJDMi1v.SecurityCenter": "Security Center",
        "w2VwCK465D.OTApp": "privacidad de Samsung TV Plus",
        "2022ePop01.SmartTV": "promoción de 2022",
        "com.samsung.tv.preview-updater": "vistas previas del inicio de Samsung",
    },
    "alexa": {
        "AQKO41xyKP.AmazonAlexa": "Amazon Alexa",
        "com.samsung.tv.alexa-client": "Alexa en segundo plano",
        "com.samsung.tv.alexa-fullscreen-app": "Alexa",
    },
    "health": {
        "samsunghealth-service-tv": "Samsung Health",
        "com.samsung.tv.health-mde-service": "Samsung Health",
        "com.samsung.tv.health-mde-service-view": "Samsung Health",
        "com.samsung.tv.health-mde-setting": "Samsung Health",
        "com.samsung.tv.health-mde-workout-tracker": "Samsung Health",
        "com.samsung.tv.lifeplus": "Samsung Health",
    },
    "smartthings": {
        "com.samsung.tizen.smartthings-client": "SmartThings",
        "com.samsung.tizen.smartthings-thing": "SmartThings",
        "com.samsung.tv.iot-hub-control": "SmartThings (domótica)",
        "com.samsung.tv.smartthingsfind-daemon": "SmartThings Find",
        "com.samsung.tv.digitalbutler-app": "SmartThings (busca dispositivos)",
        "com.samsung.tv.digitalbutler-daemon": "SmartThings (busca dispositivos)",
    },
    "art": {
        "com.samsung.tv.home.art": "modo Arte",
        "org.tizen.art-app": "modo Arte",
        "com.samsung.tv.ambient-support": "modo Ambiente",
    },
    # ⚠️ Rompe la búsqueda por voz de las apps (necesita Bixby configurado). Solo si no usas la voz.
    "bixby": {
        "com.samsung.tv.farfieldvoice": "micro manos libres «Hi Bixby»",
        "com.samsung.tv.bixby-prov": "configuración de Bixby",
        "com.samsung.tv.bixbycapsuleviewer": "visor de Bixby",
        "com.samsung.tv.utterance-recommender-core": "sugerencias de Bixby",
    },
    "applevideo": {
        "com.samsung.tv.aria-video": "app Apple TV (~100 MB en memoria)",
        "30IKH0OX8U.TestBGService": "servicio de fondo de Apple TV",
    },
    # Solo si el botón Home ya abre Mi Inicio (set-home.sh). El núcleo (csfs) se deja como reserva.
    "samsunghome": {
        "com.samsung.tv.home.media": "inicio de Samsung: pestaña de contenido (~100 MB)",
        "com.samsung.tv.home.sidebar": "inicio de Samsung: barra lateral (~40 MB)",
        "com.samsung.tv.sboard-app": "inicio de Samsung: tablero",
    },
}
DEFAULT_GROUPS = "ads,tracking,promo"
# Nunca se tocan: el sistema de voz general, HbbTV, cuentas, el núcleo del inicio de Samsung (csfs),
# el visor de TV, TV Plus, Multi View, el navegador y el mando virtual (teclas de colores).


def selected(arg):
    names = [g.strip() for g in (arg or DEFAULT_GROUPS).split(",") if g.strip()]
    bad = [g for g in names if g not in GROUPS]
    if bad:
        sys.exit("grupos desconocidos: " + ", ".join(bad) + "\ndisponibles: " + ", ".join(GROUPS))
    out = {}
    for g in names:
        out.update(GROUPS[g])
    return out


CANDIDATES = {}
DB = "/opt/dbspace/.pkgmgr_parser.db"
TOOLS = Path(__file__).resolve().parent
RECORD = TOOLS.parent / "debloat-disabled.txt"
BATCH = 4  # pocas apps por comando: cada comando tiene 45 s de límite


def state_cmd(ids):
    q = " ".join(shlex.quote(i) for i in ids)
    return ("for a in " + q + "; do s=$(sqlite3 " + DB + " \"SELECT app_disable FROM package_app_info WHERE app_id='$a';\"); "
            "echo \"$a=${s:-ausente}\"; done")


def toggle_cmd(ids, flag, want):
    lines = ["set -eu"]
    for a in ids:
        qa = shlex.quote(a)
        lines.append(f"pkgcmd -{flag} -t app -n {qa} --uid 5001 >/dev/null")
        lines.append(f"test \"$(sqlite3 {DB} \"SELECT app_disable FROM package_app_info WHERE app_id='{a}';\")\" = {want}")
        lines.append(f"echo 'OK {a}'")
    return "\n".join(lines)


def run(tv, commands):
    report = asyncio.run(probe(tv, commands=tuple(commands)))
    if not report.get("system_files_unchanged") or not report.get("staging_cleaned"):
        raise RuntimeError("la sesión de root no pasó sus comprobaciones")
    for c in report["commands"]:
        if c["exit_code"] != 0 or c["timed_out"]:
            raise RuntimeError("falló un comando:\n" + c["stdout"] + c["stderr"])
    return "".join(c["stdout"] for c in report["commands"])


def states(tv):
    out = run(tv, [state_cmd(list(CANDIDATES))]) if CANDIDATES else ''
    return dict(line.split("=", 1) for line in out.split() if "=" in line)


def inspect(tv):
    """Solo lectura: memoria libre, carga y los procesos que más memoria usan."""
    cmd = ("free -m; echo; echo carga: $(cat /proc/loadavg); echo; "
           "for p in /proc/[0-9]*; do r=$(awk '/^VmRSS/{print $2}' $p/status 2>/dev/null); "
           "[ -n \"$r\" ] && echo \"$r $(tr '\\0' ' ' < $p/cmdline 2>/dev/null | cut -c1-110)\"; done | sort -rn | head -45")
    print(run(tv, [cmd]))


def batches(ids):
    return [ids[i:i + BATCH] for i in range(0, len(ids), BATCH)]


def main():
    tv = os.environ.get("TV_IP") or sys.exit("falta TV_IP")
    mode = sys.argv[1] if len(sys.argv) > 1 else "check"
    CANDIDATES.update(selected(sys.argv[2] if len(sys.argv) > 2 else None))
    if mode == "inspect":
        inspect(tv)
    elif mode == "check":
        st = states(tv)
        for a, why in CANDIDATES.items():
            s = st.get(a, "?")
            label = {"false": "ACTIVA", "true": "desactivada", "ausente": "no existe en esta tele"}.get(s, s)
            print(f"  {label:24} {a:46} {why}")
    elif mode == "apply":
        st = states(tv)
        todo = [a for a in CANDIDATES if st.get(a) == "false"]
        if not todo:
            print("No hay nada que desactivar.")
            return
        prev = RECORD.read_text().split() if RECORD.exists() else []
        print(run(tv, [toggle_cmd(b, "D", "true") for b in batches(todo)]).strip())
        RECORD.write_text("\n".join(sorted(set(prev + todo))) + "\n")
        print(f"Desactivadas {len(todo)} apps. Lista guardada en {RECORD}")
    elif mode == "restore":
        ids = RECORD.read_text().split() if RECORD.exists() else []
        if not ids:
            print("No hay nada que restaurar.")
            return
        print(run(tv, [toggle_cmd(b, "A", "false") for b in batches(ids)]).strip())
        RECORD.unlink()
        print(f"Reactivadas {len(ids)} apps.")
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
