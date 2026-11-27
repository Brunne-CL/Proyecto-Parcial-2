# -*- coding: utf-8 -*-
"""700 comprobaciones concretas: cada caso usa la respuesta real del servidor o de la pantalla."""
import json

import pytest

from tests.catalogo700 import BACKEND, CUENTAS_PANTALLA, FRONTEND, LOGIN_ACEPTADO, LOGIN_MALO, NOMBRES
from tests.conftest import CLAVE_ADMIN

CLAVE = "ClaveSegura1"
JSON = {"content-type": "application/json"}


def pedir(contexto, metodo, ruta, cuerpo=None):
    opciones = {}
    if cuerpo is not None:
        opciones["headers"] = JSON
        opciones["data"] = json.dumps(cuerpo)
    respuesta = getattr(contexto, metodo.lower())(ruta, **opciones)
    try:
        datos = respuesta.json()
    except Exception:
        datos = {}
    return {"status": respuesta.status, "json": datos}


def alta(usuario, correo, rol="usuario", clave=CLAVE, activo=True):
    return {"usuario": usuario, "correo": correo, "rol": rol, "clave": clave, "activo": activo}


def exigir(respuesta, status, texto):
    if respuesta["status"] != status:
        raise RuntimeError(f"{texto}: {respuesta['status']} {respuesta['json']}")
    return respuesta


@pytest.fixture(scope="session")
def mundo(playwright, base_url):
    admin = playwright.request.new_context(base_url=base_url)
    anon = playwright.request.new_context(base_url=base_url)
    try:
        acceso = exigir(pedir(admin, "POST", "/api/sesion", {"usuario": "admin", "clave": CLAVE_ADMIN}), 200, "login admin")
        persona = acceso["json"]["usuario"]
        sesion = exigir(pedir(admin, "GET", "/api/sesion"), 200, "sesión")

        fichas = {}
        consultas = {}
        for nombre in NOMBRES:
            creado = exigir(
                pedir(admin, "POST", "/api/usuarios", alta(nombre, f"{nombre}@uteq.edu.mx")),
                200,
                f"alta {nombre}",
            )
            fichas[nombre] = creado["json"]
            consultas[nombre] = exigir(pedir(admin, "GET", f"/api/usuarios/{creado['json']['id']}"), 200, f"consulta {nombre}")["json"]
        listado = exigir(pedir(admin, "GET", "/api/usuarios"), 200, "listado")["json"]["usuarios"]

        invalidas = {}
        indice = 0
        for caso in BACKEND:
            if caso["tipo"] != "alta_invalida":
                continue
            indice += 1
            cuerpo = alta(f"valido{indice:03d}", f"valido{indice:03d}@uteq.edu.mx")
            cuerpo[caso["campo"]] = caso["valor"]
            invalidas[caso["id"]] = pedir(admin, "POST", "/api/usuarios", cuerpo)

        logins = []
        for usuario, clave in LOGIN_MALO:
            contexto = playwright.request.new_context(base_url=base_url)
            try:
                logins.append(pedir(contexto, "POST", "/api/sesion", {"usuario": usuario, "clave": clave}))
            finally:
                contexto.dispose()
        aceptados = []
        for usuario, clave, _esperado in LOGIN_ACEPTADO:
            contexto = playwright.request.new_context(base_url=base_url)
            try:
                aceptados.append(pedir(contexto, "POST", "/api/sesion", {"usuario": usuario, "clave": clave}))
            finally:
                contexto.dispose()

        sin_sesion = {}
        for caso in BACKEND:
            if caso["tipo"] != "sin_sesion":
                continue
            cuerpo = alta("intruso.qa", "intruso.qa@uteq.edu.mx") if caso["metodo"] in ("POST", "PUT") else None
            sin_sesion[(caso["metodo"], caso["ruta"])] = pedir(anon, caso["metodo"], caso["ruta"], cuerpo)

        base = exigir(pedir(admin, "POST", "/api/usuarios", alta("duplicado.base", "duplicado.base@uteq.edu.mx")), 200, "duplicado base")["json"]
        repetido_usuario = pedir(admin, "POST", "/api/usuarios", alta("duplicado.base", "otro.duplicado@uteq.edu.mx"))
        repetido_correo = pedir(admin, "POST", "/api/usuarios", alta("duplicado.otro", "duplicado.base@uteq.edu.mx"))

        ausentes = {
            "GET": pedir(admin, "GET", "/api/usuarios/99999"),
            "PUT": pedir(admin, "PUT", "/api/usuarios/99999", alta("nadie.qa", "nadie.qa@uteq.edu.mx")),
            "DELETE": pedir(admin, "DELETE", "/api/usuarios/99999"),
        }
        propio = persona["id"]
        protege = {
            "borrar": pedir(admin, "DELETE", f"/api/usuarios/{propio}"),
            "rol": pedir(admin, "PUT", f"/api/usuarios/{propio}", alta("admin", "admin@uteq.edu.mx", rol="usuario")),
            "activo": pedir(admin, "PUT", f"/api/usuarios/{propio}", alta("admin", "admin@uteq.edu.mx", activo=False)),
        }

        lector = exigir(pedir(admin, "POST", "/api/usuarios", alta("lector.qa", "lector.qa@uteq.edu.mx")), 200, "lector")["json"]
        cuenta = playwright.request.new_context(base_url=base_url)
        try:
            exigir(pedir(cuenta, "POST", "/api/sesion", {"usuario": "lector.qa", "clave": CLAVE}), 200, "login lector")
            lector_sesion = pedir(cuenta, "GET", "/api/sesion")
            lector_llamadas = {
                ("GET", "/api/usuarios"): pedir(cuenta, "GET", "/api/usuarios"),
                ("POST", "/api/usuarios"): pedir(cuenta, "POST", "/api/usuarios", alta("lector.alta", "lector.alta@uteq.edu.mx")),
                ("PUT", "/api/usuarios/1"): pedir(cuenta, "PUT", "/api/usuarios/1", alta("admin", "admin@uteq.edu.mx")),
                ("DELETE", "/api/usuarios/1"): pedir(cuenta, "DELETE", "/api/usuarios/1"),
            }
        finally:
            cuenta.dispose()

        editable = exigir(pedir(admin, "POST", "/api/usuarios", alta("editable.qa", "editable.qa@uteq.edu.mx")), 200, "editable")["json"]
        editado_correo = pedir(
            admin, "PUT", f"/api/usuarios/{editable['id']}",
            alta("editable.qa", "editable.nuevo@uteq.edu.mx"),
        )
        con_rol = exigir(pedir(admin, "POST", "/api/usuarios", alta("roles.qa", "roles.qa@uteq.edu.mx")), 200, "roles")["json"]
        a_admin = pedir(admin, "PUT", f"/api/usuarios/{con_rol['id']}", alta("roles.qa", "roles.qa@uteq.edu.mx", rol="admin"))
        a_usuario = pedir(admin, "PUT", f"/api/usuarios/{con_rol['id']}", alta("roles.qa", "roles.qa@uteq.edu.mx", rol="usuario"))

        estable = exigir(pedir(admin, "POST", "/api/usuarios", alta("clave.estable", "clave.estable@uteq.edu.mx")), 200, "estable")["json"]
        conserva = pedir(admin, "PUT", f"/api/usuarios/{estable['id']}", alta("clave.estable", "clave.estable@uteq.edu.mx", clave=""))
        sigue = playwright.request.new_context(base_url=base_url)
        try:
            login_conservado = pedir(sigue, "POST", "/api/sesion", {"usuario": "clave.estable", "clave": CLAVE})
        finally:
            sigue.dispose()

        cambiado = exigir(pedir(admin, "POST", "/api/usuarios", alta("clave.nueva", "clave.nueva@uteq.edu.mx")), 200, "clave nueva")["json"]
        pedir(admin, "PUT", f"/api/usuarios/{cambiado['id']}", alta("clave.nueva", "clave.nueva@uteq.edu.mx", clave="OtraClave9"))
        vieja = playwright.request.new_context(base_url=base_url)
        nueva = playwright.request.new_context(base_url=base_url)
        try:
            login_vieja = pedir(vieja, "POST", "/api/sesion", {"usuario": "clave.nueva", "clave": CLAVE})
            login_nueva = pedir(nueva, "POST", "/api/sesion", {"usuario": "clave.nueva", "clave": "OtraClave9"})
        finally:
            vieja.dispose()
            nueva.dispose()

        quieto = exigir(pedir(admin, "POST", "/api/usuarios", alta("quieto.qa", "quieto.qa@uteq.edu.mx")), 200, "quieto")["json"]
        pedir(admin, "PUT", f"/api/usuarios/{quieto['id']}", alta("quieto.qa", "quieto.qa@uteq.edu.mx", activo=False))
        bloqueado = playwright.request.new_context(base_url=base_url)
        try:
            login_inactivo = pedir(bloqueado, "POST", "/api/sesion", {"usuario": "quieto.qa", "clave": CLAVE})
        finally:
            bloqueado.dispose()

        mayus = exigir(
            pedir(admin, "POST", "/api/usuarios", alta("caso.correo", "Caso.Correo@UTEQ.EDU.MX")),
            200,
            "correo mayúsculas",
        )["json"]
        borde = exigir(
            pedir(admin, "POST", "/api/usuarios", alta("  caso.borde  ", "caso.borde@uteq.edu.mx")),
            200,
            "usuario con espacios",
        )["json"]
        temporal = exigir(pedir(admin, "POST", "/api/usuarios", alta("temporal.baja", "temporal.baja@uteq.edu.mx")), 200, "temporal")["json"]
        baja = pedir(admin, "DELETE", f"/api/usuarios/{temporal['id']}")
        consulta_baja = pedir(admin, "GET", f"/api/usuarios/{temporal['id']}")
        ocho = pedir(admin, "POST", "/api/usuarios", alta("ocho.chars", "ocho.chars@uteq.edu.mx", clave="12345678"))

        salida = playwright.request.new_context(base_url=base_url)
        try:
            exigir(pedir(salida, "POST", "/api/sesion", {"usuario": "admin", "clave": CLAVE_ADMIN}), 200, "login para salir")
            cerrado = pedir(salida, "DELETE", "/api/sesion")
            despues = pedir(salida, "GET", "/api/sesion")
        finally:
            salida.dispose()

        yield {
            "salud": pedir(anon, "GET", "/salud"),
            "metodos": {
                "POST": pedir(anon, "POST", "/salud"),
                "PUT": pedir(anon, "PUT", "/salud"),
                "DELETE": pedir(anon, "DELETE", "/salud"),
            },
            "login_admin": persona,
            "sesion": sesion["json"],
            "logout": {"cerrado": cerrado, "despues": despues},
            "sesion_anonima": pedir(playwright.request.new_context(base_url=base_url), "GET", "/api/sesion"),
            "logins": logins,
            "aceptados": aceptados,
            "sin_sesion": sin_sesion,
            "fichas": fichas,
            "consultas": consultas,
            "nombres": [fila["usuario"] for fila in listado],
            "ids": [fila["id"] for fila in listado],
            "invalidas": invalidas,
            "repetido_usuario": repetido_usuario,
            "repetido_correo": repetido_correo,
            "base_duplicado": base,
            "ausentes": ausentes,
            "protege": protege,
            "lector_llamadas": lector_llamadas,
            "lector_sesion": lector_sesion["json"],
            "lector": lector,
            "editado_correo": editado_correo,
            "a_admin": a_admin,
            "a_usuario": a_usuario,
            "conserva": conserva,
            "login_conservado": login_conservado,
            "login_vieja": login_vieja,
            "login_nueva": login_nueva,
            "login_inactivo": login_inactivo,
            "mayus": mayus,
            "borde": borde,
            "baja": baja,
            "consulta_baja": consulta_baja,
            "ocho": ocho,
            "por_usuario": {
                fila["usuario"]: fila
                for fila in exigir(pedir(admin, "GET", "/api/usuarios"), 200, "listado final")["json"]["usuarios"]
            },
        }
    finally:
        admin.dispose()
        anon.dispose()


@pytest.fixture(scope="session")
def recorrido(playwright, base_url, mundo):
    navegador = playwright.chromium.launch(headless=True)
    pagina = navegador.new_page(viewport={"width": 1280, "height": 900})
    pagina.on("dialog", lambda dialogo: dialogo.accept())
    try:
        pagina.goto(base_url + "/", wait_until="domcontentloaded")
        pagina.wait_for_selector("#form-login")
        pagina.wait_for_function(
            "() => document.querySelector(\"[data-testid='estado-sistema'] span\")?.textContent === 'operativo'"
        )
        datos = {
            "login": pagina.locator("body").inner_text(),
            "titulo": pagina.title(),
            "inputs_usuario": pagina.locator("#usuario").count(),
            "inputs_clave": pagina.locator("#form-login input[type=password]").count(),
            "boton_login": pagina.locator("#form-login button").inner_text().strip(),
        }
        pagina.fill("#usuario", "admin")
        pagina.fill("#clave", "clave-incorrecta")
        pagina.click("#form-login button")
        pagina.wait_for_selector("#mensaje-error:not([hidden])")
        datos["error"] = pagina.locator("#mensaje-error").inner_text().strip()

        pagina.fill("#clave", CLAVE_ADMIN)
        pagina.click("#form-login button")
        pagina.wait_for_selector("#tabla-usuarios")
        datos["tablero"] = pagina.locator("body").inner_text()
        datos["filas"] = pagina.evaluate(
            """() => {
                const mapa = {};
                for (const tr of document.querySelectorAll('#tabla-usuarios tbody tr')) {
                    const celdas = [...tr.children].map((td) => td.innerText.trim());
                    mapa[tr.dataset.usuario] = {
                        id: celdas[0],
                        usuario: celdas[1],
                        correo: celdas[2],
                        rol: celdas[3],
                        estado: celdas[4],
                        editar: Boolean(tr.querySelector("[data-accion='editar']")),
                        eliminar: Boolean(tr.querySelector("[data-accion='eliminar']")),
                    };
                }
                return mapa;
            }"""
        )
        for usuario, fila in datos["filas"].items():
            fila["id_api"] = mundo["por_usuario"][usuario]["id"]
        datos["ids_tabla"] = [int(fila["id"]) for fila in datos["filas"].values()]

        ediciones = {}
        for usuario, _correo, _rol, _estado in CUENTAS_PANTALLA:
            pagina.locator(f"[data-usuario='{usuario}'] [data-accion='editar']").click()
            pagina.wait_for_selector("#form-usuario h2")
            ediciones[usuario] = {
                "usuario": pagina.input_value("#f-usuario"),
                "correo": pagina.input_value("#f-correo"),
                "rol": pagina.input_value("#f-rol"),
                "activo": pagina.input_value("#f-activo"),
                "titulo": pagina.locator("#form-usuario h2").inner_text().strip(),
                "clave": pagina.locator("label[for='f-clave']").inner_text().strip(),
            }
            pagina.click("#cancelar")
            pagina.wait_for_selector("#form-usuario", state="detached")
        datos["ediciones"] = ediciones

        pagina.locator("[data-usuario='admin'] [data-accion='eliminar']").click()
        pagina.wait_for_function("() => (document.querySelector('#aviso')?.innerText || '').includes('propia')")
        datos["admin_sigue"] = {
            "aviso": pagina.locator("#aviso").inner_text().strip(),
            "filas": pagina.evaluate("() => [...document.querySelectorAll('#tabla-usuarios tbody tr')].map((tr) => tr.dataset.usuario)"),
        }

        pagina.click("#nuevo")
        pagina.wait_for_selector("#form-usuario")
        rechazos = {}
        indice = 0
        for caso in FRONTEND:
            if caso["tipo"] != "ui_rechazo":
                continue
            indice += 1
            pagina.evaluate(
                """() => {
                    const aviso = document.querySelector('#mensaje-form');
                    if (aviso) { aviso.hidden = true; aviso.textContent = ''; }
                }"""
            )
            if caso["campo"] == "usuario":
                nombre = caso["valor"]
                pagina.fill("#f-usuario", caso["valor"])
                pagina.fill("#f-correo", f"rechazo.u{indice:03d}@uteq.edu.mx")
                pagina.fill("#f-clave", CLAVE)
            else:
                nombre = f"rechazo{indice:03d}"
                pagina.fill("#f-usuario", nombre)
                pagina.fill("#f-correo", f"rechazo.c{indice:03d}@uteq.edu.mx")
                pagina.fill("#f-clave", caso["valor"])
            pagina.select_option("#f-rol", "usuario")
            pagina.click("#form-usuario button[type=submit]")
            if caso["mensaje"]:
                pagina.wait_for_function(
                    """(esperado) => {
                        const aviso = document.querySelector('#mensaje-form');
                        return Boolean(aviso && !aviso.hidden && aviso.innerText.trim() === esperado);
                    }""",
                    arg=caso["mensaje"],
                )
                texto = pagina.locator("#mensaje-form").inner_text().strip()
            else:
                texto = ""
            creado = pagina.evaluate(
                """(nombre) => [...document.querySelectorAll('#tabla-usuarios tbody tr')].some((tr) => tr.dataset.usuario === nombre)""",
                nombre,
            )
            rechazos[caso["id"]] = {"texto": texto, "creado": creado}
        datos["rechazos"] = rechazos
        if pagina.locator("#cancelar").count():
            pagina.click("#cancelar")

        pagina.click("#nuevo")
        pagina.wait_for_selector("#form-usuario")
        datos["formulario"] = pagina.locator("body").inner_text()

        pagina.fill("#f-usuario", "pantalla.demo")
        pagina.fill("#f-correo", "pantalla.demo@uteq.edu.mx")
        pagina.fill("#f-clave", CLAVE)
        pagina.click("#form-usuario button[type=submit]")
        pagina.wait_for_selector("tr[data-usuario='pantalla.demo']")
        datos["aviso_creado"] = pagina.locator("#aviso").inner_text()
        datos["tras_crear"] = pagina.locator("body").inner_text()

        pagina.locator("tr[data-usuario='pantalla.demo'] [data-accion='editar']").click()
        pagina.wait_for_selector("#f-usuario")
        pagina.fill("#f-usuario", "pantalla.demox")
        pagina.fill("#f-correo", "pantalla.demox@uteq.edu.mx")
        pagina.click("#form-usuario button[type=submit]")
        pagina.wait_for_selector("tr[data-usuario='pantalla.demox']")
        datos["aviso_editado"] = pagina.locator("#aviso").inner_text()
        datos["tras_editar"] = pagina.locator("body").inner_text()

        pagina.locator("tr[data-usuario='pantalla.demox'] [data-accion='eliminar']").click()
        pagina.wait_for_selector("tr[data-usuario='pantalla.demox']", state="detached")
        datos["aviso_eliminado"] = pagina.locator("#aviso").inner_text()
        datos["tras_eliminar"] = pagina.locator("body").inner_text()

        pagina.click("#salir")
        pagina.wait_for_selector("#form-login")
        datos["salida"] = pagina.locator("body").inner_text()
        datos["estado"] = pagina.locator("[data-testid='estado-sistema'] span").inner_text().strip()
        yield datos
    finally:
        navegador.close()


def _error(respuesta):
    return respuesta["json"].get("error", "")


def comprobar_backend(caso, mundo):
    tipo = caso["tipo"]
    if tipo == "salud":
        assert mundo["salud"]["status"] == 200
        assert mundo["salud"]["json"][caso["campo"]] == caso["esperado"]
    elif tipo == "salud_status":
        assert mundo["salud"]["status"] == caso["esperado"]
    elif tipo == "salud_sin":
        assert caso["campo"] not in mundo["salud"]["json"]
    elif tipo == "salud_tipo":
        assert mundo["salud"]["json"]["estado"] == "ok"
        assert isinstance(mundo["salud"]["json"], dict)
    elif tipo == "metodo":
        assert mundo["metodos"][caso["metodo"]]["status"] == caso["esperado"]
    elif tipo == "login_ok":
        respuesta = mundo["aceptados"][LOGIN_ACEPTADO.index((caso["usuario"], caso["clave"], caso["esperado"]))]
        assert respuesta["status"] == 200
        assert respuesta["json"]["usuario"]["usuario"] == caso["esperado"]
        assert "clave" not in respuesta["json"]["usuario"]
    elif tipo == "login_malo":
        respuesta = mundo["logins"][LOGIN_MALO.index((caso["usuario"], caso["clave"]))]
        assert respuesta["status"] == 401
        assert _error(respuesta) == "Usuario o clave incorrectos."
    elif tipo == "login_admin":
        assert mundo["login_admin"][caso["campo"]] == caso["esperado"]
    elif tipo == "login_admin_sin_clave":
        assert "clave" not in mundo["login_admin"]
    elif tipo == "login_admin_id":
        assert isinstance(mundo["login_admin"]["id"], int) and mundo["login_admin"]["id"] > 0
    elif tipo == "sesion_ok":
        assert mundo["sesion"]["autenticado"] is True
        assert mundo["sesion"]["usuario"]["usuario"] == "admin"
    elif tipo == "logout":
        assert mundo["logout"]["cerrado"]["status"] == 200
        assert mundo["logout"]["despues"]["json"]["autenticado"] is False
    elif tipo == "sesion_anonima":
        assert mundo["sesion_anonima"]["status"] == 200
        assert mundo["sesion_anonima"]["json"]["autenticado"] is False
    elif tipo == "sin_sesion":
        respuesta = mundo["sin_sesion"][(caso["metodo"], caso["ruta"])]
        assert respuesta["status"] == 401
        assert _error(respuesta) == "Debe iniciar sesión."
    elif tipo == "alta_invalida":
        respuesta = mundo["invalidas"][caso["id"]]
        assert respuesta["status"] == 422
        assert _error(respuesta) == caso["mensaje"]
    elif tipo == "ficha":
        ficha = mundo["fichas"][caso["nombre"]]
        campo = caso["campo"]
        if campo == "usuario":
            assert ficha["usuario"] == caso["nombre"]
        elif campo == "correo":
            assert ficha["correo"] == f"{caso['nombre']}@uteq.edu.mx"
        elif campo == "rol":
            assert ficha["rol"] == "usuario"
        elif campo == "activo":
            assert ficha["activo"] is True
        elif campo == "id":
            assert isinstance(ficha["id"], int) and ficha["id"] > 0
        elif campo == "sin_clave":
            assert "clave" not in ficha
        elif campo == "creado":
            assert "T" in ficha["creado"]
        elif campo == "actualizado":
            assert "T" in ficha["actualizado"]
        elif campo == "dominio":
            assert ficha["correo"].endswith("@uteq.edu.mx")
        elif campo == "mismo_instante":
            assert ficha["creado"] == ficha["actualizado"]
        elif campo == "en_listado":
            assert caso["nombre"] in mundo["nombres"]
        elif campo == "consulta":
            assert mundo["consultas"][caso["nombre"]]["correo"] == f"{caso['nombre']}@uteq.edu.mx"
        else:
            raise AssertionError(campo)
    elif tipo == "duplicado_usuario":
        assert mundo["repetido_usuario"]["status"] == 409
        assert _error(mundo["repetido_usuario"]) == "Ya existe un usuario con ese nombre o correo."
        assert mundo["base_duplicado"]["usuario"] == "duplicado.base"
    elif tipo == "duplicado_correo":
        assert mundo["repetido_correo"]["status"] == 409
        assert _error(mundo["repetido_correo"]) == "Ya existe un usuario con ese nombre o correo."
    elif tipo == "ausente":
        respuesta = mundo["ausentes"][caso["metodo"]]
        assert respuesta["status"] == 404
        assert _error(respuesta) == "El usuario no existe."
    elif tipo == "protege_admin":
        respuesta = mundo["protege"][caso["modo"]]
        assert respuesta["status"] == 409
        if caso["modo"] == "borrar":
            assert _error(respuesta) == "No puede eliminar su propia cuenta."
        else:
            assert _error(respuesta) == "Debe permanecer al menos un administrador activo."
    elif tipo == "lector":
        respuesta = mundo["lector_llamadas"][(caso["metodo"], caso["ruta"])]
        assert respuesta["status"] == 403
        assert _error(respuesta) == "Solo un administrador puede gestionar usuarios."
    elif tipo == "lector_rol":
        assert mundo["lector_sesion"]["autenticado"] is True
        assert mundo["lector_sesion"]["usuario"]["rol"] == "usuario"
        assert mundo["lector_sesion"]["usuario"]["usuario"] == "lector.qa"
    elif tipo == "editar" and caso["modo"] == "correo":
        assert mundo["editado_correo"]["status"] == 200
        assert mundo["editado_correo"]["json"]["correo"] == "editable.nuevo@uteq.edu.mx"
        assert mundo["editado_correo"]["json"]["usuario"] == "editable.qa"
    elif tipo == "editar" and caso["modo"] == "rol":
        assert mundo["a_admin"]["status"] == 200 and mundo["a_admin"]["json"]["rol"] == "admin"
        assert mundo["a_usuario"]["status"] == 200 and mundo["a_usuario"]["json"]["rol"] == "usuario"
    elif tipo == "editar" and caso["modo"] == "sin_clave":
        assert mundo["conserva"]["status"] == 200
        assert "clave" not in mundo["conserva"]["json"]
        assert mundo["login_conservado"]["status"] == 200
    elif tipo == "editar" and caso["modo"] == "clave":
        assert mundo["login_vieja"]["status"] == 401
        assert mundo["login_nueva"]["status"] == 200
        assert mundo["login_nueva"]["json"]["usuario"]["usuario"] == "clave.nueva"
    elif tipo == "editar" and caso["modo"] == "inactivo":
        assert mundo["login_inactivo"]["status"] == 401
        assert _error(mundo["login_inactivo"]) == "Usuario o clave incorrectos."
    elif tipo == "normaliza" and caso["modo"] == "correo":
        assert mundo["mayus"]["correo"] == "caso.correo@uteq.edu.mx"
    elif tipo == "normaliza" and caso["modo"] == "usuario":
        assert mundo["borde"]["usuario"] == "caso.borde"
    elif tipo == "borrar_temporal":
        assert mundo["baja"]["status"] == 200
        assert mundo["consulta_baja"]["status"] == 404
        assert _error(mundo["consulta_baja"]) == "El usuario no existe."
    elif tipo == "orden":
        assert mundo["ids"] == sorted(mundo["ids"])
        assert len(mundo["ids"]) > 1
    elif tipo == "clave_ocho":
        assert mundo["ocho"]["status"] == 200
        assert mundo["ocho"]["json"]["usuario"] == "ocho.chars"
        assert "clave" not in mundo["ocho"]["json"]
    else:
        raise AssertionError(f"Tipo sin comprobación: {tipo}")


def comprobar_frontend(caso, recorrido):
    tipo = caso["tipo"]
    if tipo == "fila":
        fila = recorrido["filas"][caso["usuario"]]
        if caso["campo"] == "id":
            assert fila["id"] == str(fila["id_api"])
            assert fila["id"].isdigit()
        else:
            assert fila[caso["campo"]] == caso["esperado"]
    elif tipo == "edicion":
        assert recorrido["ediciones"][caso["usuario"]][caso["campo"]] == caso["esperado"]
    elif tipo == "orden_visual":
        assert recorrido["ids_tabla"] == sorted(recorrido["ids_tabla"])
        assert len(recorrido["ids_tabla"]) > 1
    elif tipo == "admin_sigue":
        assert recorrido["admin_sigue"]["aviso"] == "No puede eliminar su propia cuenta."
        assert "admin" in recorrido["admin_sigue"]["filas"]
    elif tipo == "ui_rechazo":
        hecho = recorrido["rechazos"][caso["id"]]
        assert hecho["texto"] == caso["mensaje"]
        assert hecho["creado"] is False
    elif tipo == "contiene":
        assert caso["texto"] in recorrido[caso["donde"]]
    elif tipo == "ausente":
        assert caso["texto"] not in recorrido[caso["donde"]]
    elif tipo == "igual":
        assert recorrido[caso["donde"]] == caso["texto"]
    elif tipo == "cuenta":
        assert recorrido[caso["donde"]] == caso["n"]
    else:
        raise AssertionError(tipo)


@pytest.mark.backend
@pytest.mark.parametrize("caso", BACKEND, ids=[caso["id"] for caso in BACKEND])
def test_comprobacion_backend(caso, mundo):
    comprobar_backend(caso, mundo)


@pytest.mark.frontend
@pytest.mark.parametrize("caso", FRONTEND, ids=[caso["id"] for caso in FRONTEND])
def test_comprobacion_frontend(caso, recorrido):
    comprobar_frontend(caso, recorrido)
