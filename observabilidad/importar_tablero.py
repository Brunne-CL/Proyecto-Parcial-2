"""Crea el tablero y la alerta en OpenObserve a partir de tablero.json."""
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from observabilidad.publicar_evento import cargar_entorno
from observabilidad.publicar_evento import main as publicar


def token_basic():
    import base64

    usuario = os.environ.get("OO_USER", "").strip()
    clave = os.environ.get("OO_PASSWORD", "").strip()
    return base64.b64encode(f"{usuario}:{clave}".encode("utf-8")).decode("ascii")


def pedir(url, token, payload=None, metodo="POST"):
    datos = None if payload is None else json.dumps(payload).encode("utf-8")
    peticion = urllib.request.Request(
        url,
        data=datos,
        headers={"Authorization": f"Basic {token}", "Content-Type": "application/json"},
        method=metodo,
    )
    try:
        with urllib.request.urlopen(peticion, timeout=40) as respuesta:
            texto = respuesta.read().decode("utf-8", errors="replace")
            print(respuesta.status, url)
            print(texto[:700])
            return respuesta.status, texto
    except urllib.error.HTTPError as error:
        texto = error.read().decode("utf-8", errors="replace")
        print(error.code, url, file=sys.stderr)
        print(texto[:1200], file=sys.stderr)
        return error.code, texto


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
    codigo_lista, lista = pedir(f"{base}/api/{org}/dashboards", token, metodo="GET")
    ya_esta = False
    if codigo_lista < 400:
        try:
            def titulo(item):
                if item.get("title"):
                    return item["title"]
                for version in ("v8", "v7", "v6", "v5", "v4", "v3"):
                    bloque = item.get(version) or {}
                    if isinstance(bloque, dict) and bloque.get("title"):
                        return bloque["title"]
                return ""

            ya_esta = any(titulo(item) == tablero["title"] for item in json.loads(lista).get("dashboards", []))
        except json.JSONDecodeError:
            ya_esta = False
    if ya_esta:
        print("El tablero ya existe.")
    else:
        codigo, _ = pedir(f"{base}/api/{org}/dashboards", token, tablero)
        if codigo >= 400:
            return 1
    alerta = {
        "name": "Pipeline-con-fallo",
        "stream_type": "logs",
        "stream_name": "cicd",
        "is_real_time": False,
        "enabled": True,
        "description": "Una ejecución de pruebas o un despliegue terminó en fallo.",
        "query_condition": {
            "type": "sql",
            "sql": "SELECT count(*) as count FROM cicd WHERE estado = 'fallo'",
            "promql": "",
            "promql_condition": None,
            "aggregation": None,
            "vrl_function": None,
            "search_event_type": "ui",
            "multi_time_range": [],
        },
        "trigger_condition": {
            "period": 10,
            "operator": ">=",
            "threshold": 1,
            "frequency": 5,
            "frequency_type": "minutes",
            "silence": 10,
            "timezone": "UTC",
        },
        "destinations": [],
        "context_attributes": {},
        "folder_id": "default",
    }
    codigo, _ = pedir(f"{base}/api/v2/{org}/alerts?folder=default", token, alerta)
    if codigo >= 400:
        return 1
    print("Tablero y alerta creados en OpenObserve.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
