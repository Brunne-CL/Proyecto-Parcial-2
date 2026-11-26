"""Publica en OpenObserve el resultado de pruebas o de un despliegue."""
import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


def cargar_entorno():
    ruta = Path(__file__).resolve().parent.parent / ".env"
    if not ruta.exists():
        return
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        limpia = linea.strip()
        if not limpia or limpia.startswith("#") or "=" not in limpia:
            continue
        clave, valor = limpia.split("=", 1)
        os.environ.setdefault(clave.strip(), valor.strip())


def normalizar(estado):
    return {"success": "exito", "failure": "fallo", "exito": "exito", "fallo": "fallo"}[estado]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tipo", required=True, choices=["pruebas", "despliegue"])
    parser.add_argument("--estado", required=True, choices=["success", "failure", "exito", "fallo"])
    args = parser.parse_args()
    cargar_entorno()

    base = os.environ.get("OPENOBSERVE_URL", "").strip().rstrip("/")
    if not base:
        mensaje = "OPENOBSERVE_URL no está definido. No se envió el evento."
        print(mensaje)
        return 1 if os.environ.get("GITHUB_ACTIONS") == "true" else 0

    estado = normalizar(args.estado)
    organizacion = os.environ.get("OPENOBSERVE_ORG", "default").strip() or "default"
    usuario = os.environ.get("OO_USER", os.environ.get("OPENOBSERVE_USER", "")).strip()
    clave = os.environ.get("OO_PASSWORD", os.environ.get("OPENOBSERVE_PASSWORD", "")).strip()
    token = base64.b64encode(f"{usuario}:{clave}".encode("utf-8")).decode("ascii")
    evento = {
        "nivel": "error" if estado == "fallo" else "info",
        "tipo": args.tipo,
        "estado": estado,
        "commit": os.environ.get("GITHUB_SHA", "local"),
        "rama": os.environ.get("GITHUB_REF_NAME", "local"),
        "usuario": os.environ.get("GITHUB_ACTOR", os.environ.get("USERNAME", "local")),
        "repositorio": os.environ.get("GITHUB_REPOSITORY", "local"),
        "flujo": os.environ.get("GITHUB_WORKFLOW", "local"),
        "mensaje": f"{args.tipo} {estado}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    peticion = urllib.request.Request(
        f"{base}/api/{organizacion}/cicd/_json",
        data=json.dumps([evento]).encode("utf-8"),
        headers={"Authorization": f"Basic {token}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(peticion, timeout=30) as respuesta:
            print(respuesta.read().decode("utf-8", errors="replace"))
    except urllib.error.HTTPError as error:
        print(error.read().decode("utf-8", errors="replace"), file=sys.stderr)
        return 1
    print(f"Evento {args.tipo}/{estado} registrado en OpenObserve.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
