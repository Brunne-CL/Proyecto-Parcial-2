"""Crea el tablero y las alertas en OpenObserve a partir de tablero.json."""
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from observabilidad.publicar_evento import cargar_entorno
from observabilidad.publicar_evento import main as publicar


def pedir(url, token, payload, metodo="POST"):
    peticion = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Basic {token}", "Content-Type": "application/json"},
        method=metodo,
    )
    try:
        with urllib.request.urlopen(peticion, timeout=30) as respuesta:
            texto = respuesta.read().decode("utf-8", errors="replace")
            print(respuesta.status, url)
            print(texto[:500])
            return True
    except urllib.error.HTTPError as error:
        print(error.code, url, file=sys.stderr)
        print(error.read().decode("utf-8", errors="replace")[:800], file=sys.stderr)
        return False


def token_basic():
    import base64

    usuario = os.environ.get("OO_USER", "").strip()
    clave = os.environ.get("OO_PASSWORD", "").strip()
    return base64.b64encode(f"{usuario}:{clave}".encode("utf-8")).decode("ascii")


def main():
    cargar_entorno()
    base = os.environ.get("OPENOBSERVE_URL", "http://127.0.0.1:5080").rstrip("/")
    org = os.environ.get("OPENOBSERVE_ORG", "default")
    os.environ["OPENOBSERVE_URL"] = base
    sys.argv = ["publicar_evento.py", "--tipo", "pruebas", "--estado", "exito"]
    if publicar() != 0:
        return 1
    token = token_basic()
    tablero = json.loads((Path(__file__).parent / "tablero.json").read_text(encoding="utf-8"))
    pedir(f"{base}/api/{org}/dashboards", token, tablero)
    alerta = {
        "name": "Pipeline con fallo",
        "stream_type": "logs",
        "stream_name": "cicd",
        "is_real_time": False,
        "enabled": True,
        "description": "Una ejecución de pruebas o un despliegue terminó en fallo.",
        "query_condition": {
            "type": "custom",
            "sql": "SELECT count(*) as conteo FROM cicd WHERE estado = 'fallo'",
        },
        "trigger_condition": {
            "period": 10,
            "operator": ">=",
            "threshold": 1,
            "frequency": 1,
            "silence": 10,
        },
        "destinations": [],
    }
    if not pedir(f"{base}/api/{org}/alerts", token, alerta):
        pedir(f"{base}/api/{org}/cicd/alerts", token, alerta)
    print("Si el tablero no aparece, impórtelo desde la interfaz: Dashboards, Import, observabilidad/tablero.json.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
