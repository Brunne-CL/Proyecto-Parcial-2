"""Pruebas de backend con el cliente HTTP de Playwright."""
import json
import uuid

CLAVE_ADMIN = "Admin123!"


def cuerpo(respuesta):
    return respuesta.json()


def entrar(api, usuario="admin", clave=CLAVE_ADMIN):
    return api.post(
        "/api/sesion",
        headers={"content-type": "application/json"},
        data=json.dumps({"usuario": usuario, "clave": clave}),
    )


def nuevo_usuario(sufijo=None):
    token = sufijo or uuid.uuid4().hex[:8]
    return {
        "usuario": f"qa_{token}",
        "correo": f"qa_{token}@uteq.edu.mx",
        "clave": "ClaveSegura1",
        "rol": "usuario",
        "activo": True,
    }


def test_salud_ok(api):
    respuesta = api.get("/salud")
    assert respuesta.status == 200
    assert cuerpo(respuesta)["estado"] == "ok"


def test_login_incorrecto(api):
    respuesta = entrar(api, clave="no-es-la-clave")
    assert respuesta.status == 401
    assert "incorrectos" in cuerpo(respuesta)["error"]


def test_sin_sesion_no_lista(api):
    respuesta = api.get("/api/usuarios")
    assert respuesta.status == 401


def test_crud_completo(api):
    assert entrar(api).status == 200
    alta = nuevo_usuario()
    creado = api.post("/api/usuarios", headers={"content-type": "application/json"}, data=json.dumps(alta))
    assert creado.status == 200
    persona = cuerpo(creado)
    assert persona["usuario"] == alta["usuario"]
    assert "clave" not in persona

    consulta = api.get(f"/api/usuarios/{persona['id']}")
    assert consulta.status == 200
    assert cuerpo(consulta)["correo"] == alta["correo"]

    cambio = {**alta, "usuario": alta["usuario"] + "b", "correo": "editado_" + alta["correo"], "clave": ""}
    editado = api.put(
        f"/api/usuarios/{persona['id']}",
        headers={"content-type": "application/json"},
        data=json.dumps(cambio),
    )
    assert editado.status == 200
    assert cuerpo(editado)["usuario"] == cambio["usuario"]

    listado = cuerpo(api.get("/api/usuarios"))["usuarios"]
    assert any(fila["id"] == persona["id"] for fila in listado)

    borrado = api.delete(f"/api/usuarios/{persona['id']}")
    assert borrado.status == 200
    assert api.get(f"/api/usuarios/{persona['id']}").status == 404


def test_rol_usuario_no_administra(api):
    assert entrar(api).status == 200
    alta = nuevo_usuario()
    creado = cuerpo(api.post("/api/usuarios", headers={"content-type": "application/json"}, data=json.dumps(alta)))
    assert api.delete("/api/sesion").status == 200
    assert entrar(api, alta["usuario"], alta["clave"]).status == 200
    assert api.get("/api/usuarios").status == 403
    assert api.delete("/api/sesion").status == 200
    assert entrar(api).status == 200
    assert api.delete(f"/api/usuarios/{creado['id']}").status == 200


def test_validaciones(api):
    assert entrar(api).status == 200
    corto = nuevo_usuario()
    corto["clave"] = "123"
    assert api.post("/api/usuarios", headers={"content-type": "application/json"}, data=json.dumps(corto)).status == 422
    duplicado = nuevo_usuario()
    creado = cuerpo(api.post("/api/usuarios", headers={"content-type": "application/json"}, data=json.dumps(duplicado)))
    repetido = api.post("/api/usuarios", headers={"content-type": "application/json"}, data=json.dumps(duplicado))
    assert repetido.status == 409
    assert api.delete(f"/api/usuarios/{creado['id']}").status == 200


def test_no_elimina_al_ultimo_admin(api):
    assert entrar(api).status == 200
    propio = next(fila for fila in cuerpo(api.get("/api/usuarios"))["usuarios"] if fila["usuario"] == "admin")
    assert api.delete(f"/api/usuarios/{propio['id']}").status == 409
