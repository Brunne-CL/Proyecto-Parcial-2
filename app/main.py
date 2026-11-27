"""Login y CRUD de usuarios, con métricas, logs y trazas."""
import json
import logging
import os
import sqlite3
import time
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app import datos
from app.telemetria import configurar

ESTATICOS = Path(__file__).resolve().parent / "estaticos"
medidor, _ = configurar()
bitacora = logging.getLogger("gestion")

peticiones = medidor.create_counter(
    "http_requests_total",
    description="Peticiones HTTP por ruta y código de estado",
)
errores = medidor.create_counter(
    "http_errors_total",
    description="Peticiones HTTP con código 4xx o 5xx",
)
latencia = medidor.create_histogram(
    "http_request_duration_seconds",
    unit="s",
    description="Latencia de cada endpoint",
)

@asynccontextmanager
async def vida(_aplicacion):
    datos.iniciar()
    registrar("aplicacion_iniciada", fallo_forzado=fallo_forzado())
    yield


app = FastAPI(title="Gestión de usuarios", version="1.0.0", lifespan=vida)
app.add_middleware(SessionMiddleware, secret_key=os.environ.get("SECRET_KEY", "desarrollo-local-cambiar"), same_site="lax")
app.mount("/estaticos", StaticFiles(directory=ESTATICOS), name="estaticos")


def _marca_activa(valor):
    return str(valor or "").strip().lower() in {"1", "true", "si", "sí"}


def fallo_forzado():
    if _marca_activa(os.environ.get("FORZAR_FALLO")):
        return True
    ruta = Path(__file__).resolve().parent.parent / "fallo_intencional"
    if ruta.exists() and _marca_activa(ruta.read_text(encoding="utf-8")):
        return True
    return False


def registrar(evento, **campos):
    bitacora.info(json.dumps({"evento": evento, **campos}, ensure_ascii=False))


class MetricasMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        inicio = time.perf_counter()
        try:
            respuesta = await call_next(request)
        except Exception:
            bitacora.exception("excepcion no controlada en %s %s", request.method, request.url.path)
            raise
        duracion = time.perf_counter() - inicio
        ruta = request.scope.get("route")
        camino = ruta.path if ruta is not None else request.url.path
        atributos = {
            "http.method": request.method,
            "http.route": camino,
            "http.status_code": respuesta.status_code,
            "statusCode": respuesta.status_code,
        }
        peticiones.add(1, atributos)
        latencia.record(duracion, atributos)
        if respuesta.status_code >= 400:
            errores.add(1, atributos)
        registrar(
            "peticion",
            metodo=request.method,
            ruta=camino,
            statusCode=respuesta.status_code,
            latencia_s=round(duracion, 4),
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        return respuesta


app.add_middleware(MetricasMiddleware)


@app.exception_handler(HTTPException)
async def error_http(request, exc):
    if exc.status_code >= 500:
        bitacora.error(json.dumps({"evento": "error_http", "ruta": request.url.path, "estado": exc.status_code, "detalle": str(exc.detail)}, ensure_ascii=False))
    return JSONResponse({"error": exc.detail if isinstance(exc.detail, str) else "Solicitud rechazada"}, status_code=exc.status_code)


@app.exception_handler(Exception)
async def error_interno(request, exc):
    bitacora.exception("excepcion en %s", request.url.path)
    return JSONResponse({"error": "Error interno del servidor"}, status_code=500)


def actor(request):
    identificador = request.session.get("usuario_id")
    if not identificador:
        raise HTTPException(status_code=401, detail="Debe iniciar sesión.")
    persona = datos.por_id(identificador)
    if persona is None or not persona["activo"]:
        request.session.clear()
        raise HTTPException(status_code=401, detail="La sesión ya no es válida.")
    return persona


def exigir_admin(request):
    persona = actor(request)
    if persona["rol"] != "admin":
        raise HTTPException(status_code=403, detail="Solo un administrador puede gestionar usuarios.")
    return persona


def leer_usuario(payload, clave_obligatoria):
    mensaje = datos.validar_campos(
        payload.get("usuario"),
        payload.get("correo"),
        payload.get("rol"),
        payload.get("clave"),
        clave_obligatoria,
    )
    if mensaje:
        raise HTTPException(status_code=422, detail=mensaje)
    return (
        payload["usuario"].strip(),
        payload["correo"].strip().lower(),
        payload["rol"].strip(),
        (payload.get("clave") or "").strip() or None,
        bool(payload.get("activo", True)),
    )


@app.get("/")
def portada():
    return FileResponse(ESTATICOS / "index.html")


@app.get("/salud")
def salud():
    if fallo_forzado():
        bitacora.error(json.dumps({"evento": "fallo_intencional", "ruta": "/salud"}))
        raise HTTPException(status_code=503, detail="Fallo intencional para bloquear el despliegue.")
    return {"estado": "ok", "servicio": "gestion-usuarios"}


@app.get("/api/sesion")
def sesion_actual(request: Request):
    if not request.session.get("usuario_id"):
        return {"autenticado": False}
    persona = actor(request)
    return {"autenticado": True, "usuario": persona}


@app.post("/api/sesion")
async def iniciar_sesion(request: Request):
    payload = await request.json()
    fila = datos.por_usuario((payload.get("usuario") or "").strip())
    if fila is None or not fila["activo"] or not datos.verificar_clave(payload.get("clave") or "", fila["clave"]):
        registrar("login_rechazado", usuario=(payload.get("usuario") or "").strip())
        raise HTTPException(status_code=401, detail="Usuario o clave incorrectos.")
    request.session["usuario_id"] = fila["id"]
    registrar("login_correcto", usuario=fila["usuario"], id=fila["id"])
    return {"usuario": datos.publico(fila)}


@app.delete("/api/sesion")
def cerrar_sesion(request: Request):
    request.session.clear()
    registrar("logout")
    return {"ok": True}


@app.get("/api/usuarios")
def listar_usuarios(request: Request):
    exigir_admin(request)
    return {"usuarios": datos.listar()}


@app.get("/api/usuarios/{identificador}")
def obtener_usuario(identificador: int, request: Request):
    exigir_admin(request)
    persona = datos.por_id(identificador)
    if persona is None:
        raise HTTPException(status_code=404, detail="El usuario no existe.")
    return persona


@app.post("/api/usuarios")
async def crear_usuario(request: Request):
    admin = exigir_admin(request)
    usuario, correo, rol, clave, _activo = leer_usuario(await request.json(), clave_obligatoria=True)
    try:
        creado = datos.crear(usuario, correo, clave, rol)
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="Ya existe un usuario con ese nombre o correo.")
    registrar("usuario_creado", id=creado["id"], usuario=creado["usuario"], actor=admin["usuario"])
    return creado


@app.put("/api/usuarios/{identificador}")
async def actualizar_usuario(identificador: int, request: Request):
    admin = exigir_admin(request)
    actual = datos.por_id(identificador)
    if actual is None:
        raise HTTPException(status_code=404, detail="El usuario no existe.")
    usuario, correo, rol, clave, activo = leer_usuario(await request.json(), clave_obligatoria=False)
    deja_de_ser_admin = actual["rol"] == "admin" and actual["activo"] and (rol != "admin" or not activo)
    if deja_de_ser_admin and datos.contar_admins_activos(excepto=identificador) == 0:
        raise HTTPException(status_code=409, detail="Debe permanecer al menos un administrador activo.")
    try:
        guardado = datos.actualizar(identificador, usuario, correo, rol, activo, clave)
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="Ya existe un usuario con ese nombre o correo.")
    registrar("usuario_actualizado", id=identificador, usuario=guardado["usuario"], actor=admin["usuario"])
    return guardado


@app.delete("/api/usuarios/{identificador}")
def borrar_usuario(identificador: int, request: Request):
    admin = exigir_admin(request)
    actual = datos.por_id(identificador)
    if actual is None:
        raise HTTPException(status_code=404, detail="El usuario no existe.")
    if actual["id"] == admin["id"]:
        raise HTTPException(status_code=409, detail="No puede eliminar su propia cuenta.")
    if actual["rol"] == "admin" and actual["activo"] and datos.contar_admins_activos(excepto=identificador) == 0:
        raise HTTPException(status_code=409, detail="Debe permanecer al menos un administrador activo.")
    datos.eliminar(identificador)
    registrar("usuario_eliminado", id=identificador, usuario=actual["usuario"], actor=admin["usuario"])
    return {"ok": True}


FastAPIInstrumentor.instrument_app(app)
