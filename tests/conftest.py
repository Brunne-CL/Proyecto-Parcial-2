"""Arranque del servidor de pruebas y recolección de resultados."""
import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
EVIDENCIAS = RAIZ / "evidencias"
PUERTO = 8765
CLAVE_ADMIN = "Admin123!"
INICIO = time.time()
RESULTADOS = []


def _libre(puerto):
    with socket.socket() as sonda:
        sonda.settimeout(0.2)
        return sonda.connect_ex(("127.0.0.1", puerto)) != 0


def esperar(url, proceso, segundos=20):
    limite = time.time() + segundos
    while time.time() < limite:
        if proceso.poll() is not None:
            raise RuntimeError(f"El servidor terminó con código {proceso.returncode}")
        try:
            with urllib.request.urlopen(url, timeout=1) as respuesta:
                if respuesta.status == 200:
                    return
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            time.sleep(0.2)
    raise RuntimeError(f"El servidor no respondió en {url}")


@pytest.fixture(scope="session")
def servidor():
    if not _libre(PUERTO):
        raise RuntimeError(f"El puerto {PUERTO} está ocupado.")
    base = EVIDENCIAS / "usuarios-prueba.db"
    if base.exists():
        base.unlink()
    EVIDENCIAS.mkdir(parents=True, exist_ok=True)
    entorno = os.environ.copy()
    entorno.update(
        {
            "DATABASE_PATH": str(base),
            "SECRET_KEY": "pruebas-parcial2",
            "FORZAR_FALLO": "0",
            "ADMIN_USUARIO": "admin",
            "ADMIN_CLAVE": CLAVE_ADMIN,
            "ADMIN_CORREO": "admin@uteq.edu.mx",
            "OTEL_EXPORTER_OTLP_ENDPOINT": "",
            "ENTORNO": "pruebas",
        }
    )
    bitacora = open(EVIDENCIAS / "servidor.log", "w", encoding="utf-8")
    proceso = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(PUERTO)],
        cwd=RAIZ,
        env=entorno,
        stdout=bitacora,
        stderr=subprocess.STDOUT,
    )
    try:
        esperar(f"http://127.0.0.1:{PUERTO}/salud", proceso)
        yield f"http://127.0.0.1:{PUERTO}"
    finally:
        proceso.terminate()
        try:
            proceso.wait(timeout=8)
        except subprocess.TimeoutExpired:
            proceso.kill()
        bitacora.close()


@pytest.fixture(scope="session")
def base_url(servidor):
    return servidor


@pytest.fixture
def api(playwright, base_url):
    contexto = playwright.request.new_context(base_url=base_url)
    yield contexto
    contexto.dispose()


def pytest_runtest_logreport(report):
    if report.when != "call":
        return
    RESULTADOS.append(
        {
            "nombre": report.nodeid.split("::")[-1],
            "nodo": report.nodeid,
            "estado": "CORRECTO" if report.passed else "FALLO",
            "duracion_s": round(report.duration, 3),
        }
    )


def pytest_sessionfinish(session, exitstatus):
    EVIDENCIAS.mkdir(parents=True, exist_ok=True)
    resumen = {
        "fecha": time.strftime("%d de noviembre de 2026"),
        "lugar": "Querétaro",
        "duracion_s": round(time.time() - INICIO, 2),
        "exitstatus": exitstatus,
        "pruebas": RESULTADOS,
        "python": sys.version.split()[0],
    }
    (EVIDENCIAS / "resultados.json").write_text(json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8")
