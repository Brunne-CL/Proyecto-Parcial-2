"""API comprobada con la biblioteca estándar, para el reporte generado en Alpine."""
import json
import urllib.error
import urllib.request
from http.cookiejar import CookieJar

from tests.conftest import CLAVE_ADMIN


class Cliente:
    def __init__(self, base):
        self.base = base.rstrip("/")
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(CookieJar()))

    def pedir(self, metodo, ruta, cuerpo=None):
        datos = None
        cabeceras = {}
        if cuerpo is not None:
            datos = json.dumps(cuerpo).encode("utf-8")
            cabeceras["Content-Type"] = "application/json"
        peticion = urllib.request.Request(self.base + ruta, data=datos, headers=cabeceras, method=metodo)
        try:
            with self.opener.open(peticion, timeout=10) as respuesta:
                crudo = respuesta.read()
                estado = respuesta.status
        except urllib.error.HTTPError as error:
            crudo = error.read()
            estado = error.code
        try:
            payload = json.loads(crudo.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            payload = {}
        return estado, payload


def cliente(base_url):
    return Cliente(base_url)


def test_salud_ok(base_url):
    estado, payload = cliente(base_url).pedir("GET", "/salud")
    assert estado == 200
    assert payload["estado"] == "ok"


def test_login_incorrecto(base_url):
    estado, payload = cliente(base_url).pedir("POST", "/api/sesion", {"usuario": "admin", "clave": "no-es-la-clave"})
    assert estado == 401
    assert "incorrectos" in payload["error"]


def test_sin_sesion_no_lista(base_url):
    estado, _payload = cliente(base_url).pedir("GET", "/api/usuarios")
    assert estado == 401


def test_crud_completo(base_url):
    api = cliente(base_url)
    assert api.pedir("POST", "/api/sesion", {"usuario": "admin", "clave": CLAVE_ADMIN})[0] == 200
    alta = {
        "usuario": "alpine_qa",
        "correo": "alpine_qa@uteq.edu.mx",
        "clave": "ClaveSegura1",
        "rol": "usuario",
        "activo": True,
    }
    estado, persona = api.pedir("POST", "/api/usuarios", alta)
    assert estado == 200
    assert persona["usuario"] == alta["usuario"]
    assert "clave" not in persona

    estado, consulta = api.pedir("GET", f"/api/usuarios/{persona['id']}")
    assert estado == 200
    assert consulta["correo"] == alta["correo"]

    cambio = {**alta, "usuario": "alpine_qb", "correo": "alpine_qb@uteq.edu.mx", "clave": ""}
    estado, editado = api.pedir("PUT", f"/api/usuarios/{persona['id']}", cambio)
    assert estado == 200
    assert editado["usuario"] == "alpine_qb"

    estado, listado = api.pedir("GET", "/api/usuarios")
    assert estado == 200
    assert any(fila["id"] == persona["id"] for fila in listado["usuarios"])

    assert api.pedir("DELETE", f"/api/usuarios/{persona['id']}")[0] == 200
    assert api.pedir("GET", f"/api/usuarios/{persona['id']}")[0] == 404
