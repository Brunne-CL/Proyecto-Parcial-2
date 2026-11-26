"""El fallo intencional debe verse en /salud y en la interfaz, para que el pipeline lo detenga."""
import os
import subprocess
import sys
import urllib.error
import urllib.request

from playwright.sync_api import expect

from tests.conftest import EVIDENCIAS, RAIZ, esperar


def test_fallo_intencional_en_endpoint_y_pantalla(page):
    base = EVIDENCIAS / "usuarios-fallo.db"
    if base.exists():
        base.unlink()
    entorno = os.environ.copy()
    entorno.update(
        {
            "DATABASE_PATH": str(base),
            "SECRET_KEY": "pruebas-fallo",
            "FORZAR_FALLO": "1",
            "OTEL_EXPORTER_OTLP_ENDPOINT": "",
            "ADMIN_USUARIO": "admin",
            "ADMIN_CLAVE": "Admin123!",
        }
    )
    proceso = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8766"],
        cwd=RAIZ,
        env=entorno,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        esperar("http://127.0.0.1:8766/", proceso)
        try:
            urllib.request.urlopen("http://127.0.0.1:8766/salud", timeout=5)
            raise AssertionError("/salud respondió 200 y debía fallar")
        except urllib.error.HTTPError as error:
            assert error.code == 503
        page.set_viewport_size({"width": 1280, "height": 800})
        page.goto("http://127.0.0.1:8766/")
        expect(page.locator("[data-testid='estado-sistema']")).to_contain_text("fallo intencional")
        EVIDENCIAS.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(EVIDENCIAS / "09_fallo_intencional.png"), full_page=True)
    finally:
        proceso.terminate()
        try:
            proceso.wait(timeout=8)
        except subprocess.TimeoutExpired:
            proceso.kill()
