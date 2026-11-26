"""Pruebas de interfaz: login y CRUD de usuarios."""
import uuid

from playwright.sync_api import expect

from tests.conftest import CLAVE_ADMIN, EVIDENCIAS

EVIDENCIAS.mkdir(parents=True, exist_ok=True)


def captura(page, nombre):
    page.screenshot(path=str(EVIDENCIAS / nombre), full_page=True)


def entrar(page, base_url):
    page.goto(base_url + "/")
    expect(page.locator("#form-login")).to_be_visible()
    page.fill("#usuario", "admin")
    page.fill("#clave", CLAVE_ADMIN)
    page.click("button[type=submit]")
    expect(page.locator("#tabla-usuarios")).to_be_visible()


def test_pantalla_de_acceso(page, base_url):
    page.set_viewport_size({"width": 1280, "height": 800})
    page.goto(base_url + "/")
    expect(page.locator("#form-login")).to_be_visible()
    expect(page.locator("[data-testid='estado-sistema']")).to_contain_text("operativo")
    captura(page, "01_login.png")


def test_login_invalido(page, base_url):
    page.goto(base_url + "/")
    expect(page.locator("#form-login")).to_be_visible()
    page.fill("#usuario", "admin")
    page.fill("#clave", "clave-incorrecta")
    page.click("button[type=submit]")
    expect(page.locator("#mensaje-error")).to_contain_text("incorrectos")
    captura(page, "02_login_invalido.png")


def test_crud_en_pantalla(page, base_url):
    token = uuid.uuid4().hex[:8]
    usuario = f"pantalla_{token}"
    correo = f"{usuario}@uteq.edu.mx"
    entrar(page, base_url)
    captura(page, "03_listado.png")

    page.click("#nuevo")
    expect(page.locator("#form-usuario")).to_be_visible()
    page.fill("#f-usuario", usuario)
    page.fill("#f-correo", correo)
    page.fill("#f-clave", "ClaveSegura1")
    captura(page, "04_alta.png")
    page.click("#form-usuario button[type=submit]")
    fila = page.locator(f"tr[data-usuario='{usuario}']")
    expect(fila).to_be_visible()
    expect(page.locator("#aviso")).to_contain_text("creado")
    captura(page, "05_creado.png")

    fila.locator("[data-accion='editar']").click()
    expect(page.locator("#f-usuario")).to_have_value(usuario)
    page.fill("#f-usuario", usuario + "x")
    page.click("#form-usuario button[type=submit]")
    expect(page.locator(f"tr[data-usuario='{usuario}x']")).to_be_visible()
    captura(page, "06_editado.png")

    page.once("dialog", lambda dialogo: dialogo.accept())
    page.locator(f"tr[data-usuario='{usuario}x'] [data-accion='eliminar']").click()
    expect(page.locator(f"tr[data-usuario='{usuario}x']")).to_have_count(0)
    captura(page, "07_eliminado.png")

    page.click("#salir")
    expect(page.locator("#form-login")).to_be_visible()
    captura(page, "08_salida.png")
