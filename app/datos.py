"""Persistencia SQLite del CRUD de usuarios."""
import hashlib
import hmac
import os
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path

from opentelemetry import trace

_candado = threading.Lock()
ROLES = ("admin", "usuario")


def ruta_base():
    configurada = os.environ.get("DATABASE_PATH", "").strip()
    if configurada:
        return Path(configurada)
    return Path(__file__).resolve().parent.parent / "data" / "usuarios.db"


def _conectar():
    ruta = ruta_base()
    ruta.parent.mkdir(parents=True, exist_ok=True)
    conexion = sqlite3.connect(ruta, timeout=10)
    conexion.row_factory = sqlite3.Row
    conexion.execute("PRAGMA foreign_keys = ON")
    return conexion


def _consultar(sql, parametros=(), una=False):
    trazador = trace.get_tracer("gestion.datos")
    with trazador.start_as_current_span("db.query") as tramo:
        tramo.set_attribute("db.system.name", "sqlite")
        tramo.set_attribute("db.query.text", " ".join(sql.split()))
        with _candado:
            with _conectar() as conexion:
                cursor = conexion.execute(sql, parametros)
                if sql.lstrip().upper().startswith("SELECT"):
                    filas = cursor.fetchall()
                    if una:
                        return filas[0] if filas else None
                    return filas
                conexion.commit()
                return cursor.lastrowid


def iniciar():
    _consultar(
        """
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT NOT NULL UNIQUE COLLATE NOCASE,
            correo TEXT NOT NULL UNIQUE COLLATE NOCASE,
            clave TEXT NOT NULL,
            rol TEXT NOT NULL CHECK (rol IN ('admin', 'usuario')),
            activo INTEGER NOT NULL DEFAULT 1,
            creado TEXT NOT NULL,
            actualizado TEXT NOT NULL
        )
        """
    )
    if _consultar("SELECT id FROM usuarios LIMIT 1", una=True) is None:
        ahora = _ahora()
        _consultar(
            """
            INSERT INTO usuarios (usuario, correo, clave, rol, activo, creado, actualizado)
            VALUES (?, ?, ?, 'admin', 1, ?, ?)
            """,
            (
                os.environ.get("ADMIN_USUARIO", "admin").strip() or "admin",
                os.environ.get("ADMIN_CORREO", "admin@uteq.edu.mx").strip() or "admin@uteq.edu.mx",
                hash_clave(os.environ.get("ADMIN_CLAVE", "Admin123!")),
                ahora,
                ahora,
            ),
        )


def hash_clave(clave):
    sal = os.urandom(16).hex()
    resumen = hashlib.pbkdf2_hmac("sha256", clave.encode("utf-8"), sal.encode("ascii"), 120_000).hex()
    return f"{sal}${resumen}"


def verificar_clave(clave, almacenada):
    sal, resumen = almacenada.split("$", 1)
    prueba = hashlib.pbkdf2_hmac("sha256", clave.encode("utf-8"), sal.encode("ascii"), 120_000).hex()
    return hmac.compare_digest(prueba, resumen)


def _ahora():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def publico(fila):
    return {
        "id": fila["id"],
        "usuario": fila["usuario"],
        "correo": fila["correo"],
        "rol": fila["rol"],
        "activo": bool(fila["activo"]),
        "creado": fila["creado"],
        "actualizado": fila["actualizado"],
    }


def por_id(identificador):
    fila = _consultar("SELECT * FROM usuarios WHERE id = ?", (identificador,), una=True)
    return publico(fila) if fila else None


def por_usuario(usuario):
    return _consultar("SELECT * FROM usuarios WHERE usuario = ?", (usuario,), una=True)


def listar():
    filas = _consultar("SELECT * FROM usuarios ORDER BY id")
    return [publico(fila) for fila in filas]


def crear(usuario, correo, clave, rol):
    ahora = _ahora()
    identificador = _consultar(
        """
        INSERT INTO usuarios (usuario, correo, clave, rol, activo, creado, actualizado)
        VALUES (?, ?, ?, ?, 1, ?, ?)
        """,
        (usuario, correo, hash_clave(clave), rol, ahora, ahora),
    )
    return por_id(identificador)


def actualizar(identificador, usuario, correo, rol, activo, clave=None):
    if clave:
        _consultar(
            """
            UPDATE usuarios
               SET usuario = ?, correo = ?, rol = ?, activo = ?, clave = ?, actualizado = ?
             WHERE id = ?
            """,
            (usuario, correo, rol, int(activo), hash_clave(clave), _ahora(), identificador),
        )
    else:
        _consultar(
            """
            UPDATE usuarios
               SET usuario = ?, correo = ?, rol = ?, activo = ?, actualizado = ?
             WHERE id = ?
            """,
            (usuario, correo, rol, int(activo), _ahora(), identificador),
        )
    return por_id(identificador)


def eliminar(identificador):
    _consultar("DELETE FROM usuarios WHERE id = ?", (identificador,))


def contar_admins_activos(excepto=None):
    if excepto is None:
        fila = _consultar(
            "SELECT COUNT(*) AS total FROM usuarios WHERE rol = 'admin' AND activo = 1",
            una=True,
        )
    else:
        fila = _consultar(
            "SELECT COUNT(*) AS total FROM usuarios WHERE rol = 'admin' AND activo = 1 AND id != ?",
            (excepto,),
            una=True,
        )
    return fila["total"]


def validar_campos(usuario, correo, rol, clave=None, clave_obligatoria=False):
    usuario = (usuario or "").strip()
    correo = (correo or "").strip().lower()
    rol = (rol or "").strip()
    if not 3 <= len(usuario) <= 32 or not usuario.replace(".", "").replace("_", "").isalnum():
        return "El usuario debe tener entre 3 y 32 caracteres, letras, números, punto o guion bajo."
    if "@" not in correo or "." not in correo.split("@")[-1] or len(correo) > 120:
        return "El correo no tiene un formato válido."
    if rol not in ROLES:
        return "El rol debe ser admin o usuario."
    if clave_obligatoria and not clave:
        return "La clave es obligatoria."
    if clave and len(clave) < 8:
        return "La clave debe tener al menos 8 caracteres."
    return None
