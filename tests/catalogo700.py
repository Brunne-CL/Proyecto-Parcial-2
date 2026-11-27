# -*- coding: utf-8 -*-
"""Catálogo de 700 comprobaciones concretas del login y del CRUD."""

MENSAJE_USUARIO = "El usuario debe tener entre 3 y 32 caracteres, letras, números, punto o guion bajo."
MENSAJE_CORREO = "El correo no tiene un formato válido."
MENSAJE_ROL = "El rol debe ser admin o usuario."
MENSAJE_CLAVE = "La clave debe tener al menos 8 caracteres."
MENSAJE_CLAVE_OBLIGATORIA = "La clave es obligatoria."

NOMBRES = [
    "ana.lopez", "bruno.caldera", "carlos.diaz", "diana.ruiz", "elena.mora",
    "fernando.gil", "gabriela.paz", "hector.nunez", "irene.solis", "javier.ortiz",
    "karla.mendez", "luis.herrera", "maria.leon", "natalia.cruz", "oscar.vega",
    "paola.rios", "quique.salas", "rosa.ibarra", "sergio.luna", "teresa.campos",
    "ulises.prado", "valeria.soto", "walter.guzman", "ximena.paredes", "yolanda.bravo",
    "zoe.castro", "adrian.mora", "beatriz.leon", "cesar.ramos",     "jimena.carrillo", "kevin.santos", "liliana.meza", "marco.aranda", "nadia.falcon",
    "abc", "a.b", "a_b", "user123", "n" * 32,
    "pablo.reyes", "raquel.ibanez", "tomas.aguilar", "ursula.beltran", "vicente.ochoa",
]

USUARIOS_INVALIDOS = [
    "", "a", "ab", " ", "   ", "a b", "a-b", "a@b", "user!", "a/b",
    "a\\b", "a+b", "<script>", "a" * 33, "a" * 40, "a" * 64, "tab\tuser",
    "' OR 1=1", "..", "___", "nombre apellido", "user$", "aa%", "user#1",
    "user&co", "user,1", "user;1", "user:1", "user?1", "(user)", "[user]",
    "{user}", "a*b", "a=b", "a|b", "a~b",
]

CORREOS_INVALIDOS = [
    "", "sinarroba", "a@", "a@b", "a@bc", "correo", "plano", "nombre",
    "a@localhost", "usuario@", "@", "a@uteq", "admin@", "solo@punto",
    "a@com", "a@mx", "correo@", "@@@", "a@@", "@@", "a@uteq@edu",
    "a@uteq,edu", "a@uteq;edu", "sin-arroba.edu", "usuario.uteq",
    "gestión", "12345", "clave", "root", "uteq", "a@b c", "a@b\tc",
    "correo sin punto", "admin.uteq.edu.mx", "solo el nombre",
    "sin@", "x@y", "a@z", "hola mundo", "user name", "foo@bar", "n@",
]

CLAVES_INVALIDAS = ["", "1", "12", "123", "1234", "12345", "123456", "1234567", "abcdefg", "corta", "Clave1", "       "]
CLAVES_LIMITE = ["a", "ab", "abc", "abcd", "abcde", "abcdef", "zzzzzzz"]

ROLES_INVALIDOS = ["", "root", "ADMIN", "User", "super", "guest", "docente", "alumno", "Admin", "USUARIO", "operador", "invitado"]

LOGIN_ACEPTADO = [
    ("ADMIN", "Admin123!", "admin"),
    ("admin ", "Admin123!", "admin"),
    ("bruno.caldera", "ClaveSegura1", "bruno.caldera"),
]

LOGIN_MALO = [
    ("admin", "no-es-la-clave"),
    ("admin", ""),
    ("admin", "admin"),
    ("admin", "Admin123"),
    ("admin", "admin123!"),
    ("", "Admin123!"),
    ("", ""),
    ("nadie", "Admin123!"),
    ("lector.qa", "incorrecta"),
    ("admin", "clave-incorrecta"),
    ("admin", " " * 8),
    ("admin", "Admin123! "),
    ("root", "Admin123!"),
    ("usuario", "usuario"),
    ("admin", "12345678"),
    ("admin", "password"),
    ("admin", "' OR '1'='1"),
]

RUTAS_SIN_SESION = [
    ("GET", "/api/usuarios"),
    ("GET", "/api/usuarios/1"),
    ("POST", "/api/usuarios"),
    ("PUT", "/api/usuarios/1"),
    ("DELETE", "/api/usuarios/1"),
]

FRASES_LOGIN = [
    "Gestión de usuarios",
    "Acceso y administración de cuentas",
    "Iniciar sesión",
    "Use la cuenta de administrador para gestionar usuarios.",
    "Usuario",
    "Clave",
    "Entrar",
    "operativo",
]

ENCABEZADOS = ["Id", "Usuario", "Correo", "Rol", "Estado"]
BOTONES_LISTA = ["Nuevo usuario", "Salir", "Editar", "Eliminar"]
FRASES_FORMULARIO = [
    "Nuevo usuario", "Correo", "Rol", "Estado", "Clave", "Guardar", "Cancelar",
    "usuario", "admin", "activo", "inactivo",
]
AUSENTES_EN_LOGIN = ["Nuevo usuario", "Eliminar", "Sesión de admin", "Usuario creado.", "traceback", "pbkdf2"]

CUENTAS_PANTALLA = [("admin", "admin@uteq.edu.mx", "admin", "activo")]
CUENTAS_PANTALLA += [(nombre, f"{nombre}@uteq.edu.mx", "usuario", "activo") for nombre in NOMBRES]
CUENTAS_PANTALLA += [
    ("duplicado.base", "duplicado.base@uteq.edu.mx", "usuario", "activo"),
    ("lector.qa", "lector.qa@uteq.edu.mx", "usuario", "activo"),
    ("editable.qa", "editable.nuevo@uteq.edu.mx", "usuario", "activo"),
    ("roles.qa", "roles.qa@uteq.edu.mx", "usuario", "activo"),
    ("clave.estable", "clave.estable@uteq.edu.mx", "usuario", "activo"),
    ("clave.nueva", "clave.nueva@uteq.edu.mx", "usuario", "activo"),
    ("quieto.qa", "quieto.qa@uteq.edu.mx", "usuario", "inactivo"),
    ("caso.correo", "caso.correo@uteq.edu.mx", "usuario", "activo"),
    ("caso.borde", "caso.borde@uteq.edu.mx", "usuario", "activo"),
    ("ocho.chars", "ocho.chars@uteq.edu.mx", "usuario", "activo"),
]


def _caso(grupo, identificador, descripcion, **datos):
    return {"grupo": grupo, "id": identificador, "descripcion": descripcion, **datos}


def construir():
    backend = []
    frontend = []

    backend.append(_caso("Salud", "salud-estado-ok", "GET /salud responde estado ok.", tipo="salud", campo="estado", esperado="ok"))
    backend.append(_caso("Salud", "salud-servicio", "GET /salud identifica el servicio gestion-usuarios.", tipo="salud", campo="servicio", esperado="gestion-usuarios"))
    backend.append(_caso("Salud", "salud-codigo-200", "GET /salud responde 200.", tipo="salud_status", esperado=200))
    backend.append(_caso("Salud", "salud-sin-clave", "GET /salud no devuelve una clave.", tipo="salud_sin", campo="clave"))
    backend.append(_caso("Salud", "salud-json", "GET /salud responde JSON.", tipo="salud_tipo"))
    backend.append(_caso("Salud", "salud-post-no-permitido", "POST /salud no está permitido.", tipo="metodo", metodo="POST", ruta="/salud", esperado=405))
    backend.append(_caso("Salud", "salud-put-no-permitido", "PUT /salud no está permitido.", tipo="metodo", metodo="PUT", ruta="/salud", esperado=405))
    backend.append(_caso("Salud", "salud-delete-no-permitido", "DELETE /salud no está permitido.", tipo="metodo", metodo="DELETE", ruta="/salud", esperado=405))

    for indice, (usuario, clave, esperado) in enumerate(LOGIN_ACEPTADO, start=1):
        backend.append(_caso(
            "Login", f"login-acepta-{indice:02d}-{_slug(usuario)}",
            f"«{usuario}» entra y la sesión queda como {esperado}.",
            tipo="login_ok", usuario=usuario, clave=clave, esperado=esperado,
        ))

    for indice, (usuario, clave) in enumerate(LOGIN_MALO, start=1):
        backend.append(_caso(
            "Login", f"login-rechaza-{indice:02d}-{usuario or 'vacio'}",
            f"El acceso de «{usuario or 'vacío'}» con esa clave se rechaza.",
            tipo="login_malo", usuario=usuario, clave=clave,
        ))

    for campo, esperado in (
        ("usuario", "admin"),
        ("correo", "admin@uteq.edu.mx"),
        ("rol", "admin"),
        ("activo", True),
    ):
        backend.append(_caso("Login", f"login-admin-{campo}", f"El administrador autenticado trae {campo} = {esperado}.", tipo="login_admin", campo=campo, esperado=esperado))
    backend.append(_caso("Login", "login-admin-sin-clave", "La respuesta de login no incluye la clave.", tipo="login_admin_sin_clave"))
    backend.append(_caso("Login", "login-admin-id-entero", "El id del administrador es un entero positivo.", tipo="login_admin_id"))
    backend.append(_caso("Login", "sesion-autenticado", "GET /api/sesion confirma la sesión del administrador.", tipo="sesion_ok"))
    backend.append(_caso("Login", "logout-limpia", "DELETE /api/sesion cierra la sesión.", tipo="logout"))
    backend.append(_caso("Sesión", "sin-sesion-consulta", "GET /api/sesion sin cookie no está autenticado.", tipo="sesion_anonima"))

    for metodo, ruta in RUTAS_SIN_SESION:
        backend.append(_caso(
            "Sesión", f"sin-sesion-{metodo.lower()}-{ruta.strip('/').replace('/', '-')}",
            f"{metodo} {ruta} sin sesión responde 401.",
            tipo="sin_sesion", metodo=metodo, ruta=ruta,
        ))

    for indice, usuario in enumerate(USUARIOS_INVALIDOS, start=1):
        backend.append(_caso(
            "Validación", f"usuario-invalido-{indice:02d}-{_slug(usuario)}",
            f"El usuario «{usuario or 'vacío'}» se rechaza.",
            tipo="alta_invalida", campo="usuario", valor=usuario, mensaje=MENSAJE_USUARIO,
        ))
    backend.append(_caso("Validación", "usuario-solo-espacios", "Un usuario de solo espacios se rechaza.", tipo="alta_invalida", campo="usuario", valor="   ", mensaje=MENSAJE_USUARIO))

    for indice, correo in enumerate(CORREOS_INVALIDOS, start=1):
        backend.append(_caso(
            "Validación", f"correo-invalido-{indice:02d}-{_slug(correo)}",
            f"El correo «{correo or 'vacío'}» se rechaza.",
            tipo="alta_invalida", campo="correo", valor=correo, mensaje=MENSAJE_CORREO,
        ))

    for indice, clave in enumerate(CLAVES_INVALIDAS + CLAVES_LIMITE, start=1):
        backend.append(_caso(
            "Validación", f"clave-invalida-{indice:02d}-{len(clave)}",
            f"La clave de {len(clave)} caracteres se rechaza.",
            tipo="alta_invalida", campo="clave", valor=clave,
            mensaje=MENSAJE_CLAVE_OBLIGATORIA if clave == "" else MENSAJE_CLAVE,
        ))

    for indice, rol in enumerate(ROLES_INVALIDOS, start=1):
        backend.append(_caso(
            "Validación", f"rol-invalido-{indice:02d}-{_slug(rol)}",
            f"El rol «{rol or 'vacío'}» se rechaza.",
            tipo="alta_invalida", campo="rol", valor=rol, mensaje=MENSAJE_ROL,
        ))

    for nombre in NOMBRES:
        for campo, descripcion in (
            ("usuario", f"El alta de {nombre} guarda ese usuario."),
            ("correo", f"El alta de {nombre} guarda {nombre}@uteq.edu.mx."),
            ("rol", f"El alta de {nombre} queda con rol usuario."),
            ("activo", f"El alta de {nombre} queda activa."),
            ("id", f"El alta de {nombre} recibe un id entero."),
            ("sin_clave", f"El alta de {nombre} no devuelve la clave."),
            ("creado", f"El alta de {nombre} trae fecha de creación."),
            ("actualizado", f"El alta de {nombre} trae fecha de actualización."),
            ("dominio", f"El correo de {nombre} termina en @uteq.edu.mx."),
            ("mismo_instante", f"Al crear {nombre}, creado y actualizado coinciden."),
            ("en_listado", f"El listado incluye a {nombre}."),
            ("consulta", f"GET del id de {nombre} devuelve su correo."),
        ):
            backend.append(_caso("CRUD", f"alta-{nombre}-{campo}", descripcion, tipo="ficha", nombre=nombre, campo=campo))

    backend.append(_caso("Reglas", "duplicado-usuario", "No se puede repetir el usuario duplicado.base.", tipo="duplicado_usuario"))
    backend.append(_caso("Reglas", "duplicado-correo", "No se puede repetir el correo de duplicado.base.", tipo="duplicado_correo"))
    backend.append(_caso("Reglas", "no-existe-get", "GET de un id inexistente responde 404.", tipo="ausente", metodo="GET"))
    backend.append(_caso("Reglas", "no-existe-put", "PUT de un id inexistente responde 404.", tipo="ausente", metodo="PUT"))
    backend.append(_caso("Reglas", "no-existe-delete", "DELETE de un id inexistente responde 404.", tipo="ausente", metodo="DELETE"))
    backend.append(_caso("Reglas", "no-borra-admin", "El administrador no puede eliminarse a sí mismo.", tipo="protege_admin", modo="borrar"))
    backend.append(_caso("Reglas", "no-degrada-admin", "No se puede quitar el rol al único administrador.", tipo="protege_admin", modo="rol"))
    backend.append(_caso("Reglas", "no-desactiva-admin", "No se puede desactivar al único administrador.", tipo="protege_admin", modo="activo"))
    backend.append(_caso("Reglas", "lector-no-lista", "Una cuenta usuario recibe 403 al listar.", tipo="lector", metodo="GET", ruta="/api/usuarios"))
    backend.append(_caso("Reglas", "lector-no-crea", "Una cuenta usuario recibe 403 al crear.", tipo="lector", metodo="POST", ruta="/api/usuarios"))
    backend.append(_caso("Reglas", "lector-no-edita", "Una cuenta usuario recibe 403 al editar.", tipo="lector", metodo="PUT", ruta="/api/usuarios/1"))
    backend.append(_caso("Reglas", "lector-no-borra", "Una cuenta usuario recibe 403 al eliminar.", tipo="lector", metodo="DELETE", ruta="/api/usuarios/1"))
    backend.append(_caso("Reglas", "lector-rol", "La sesión del lector informa rol usuario.", tipo="lector_rol"))
    backend.append(_caso("Reglas", "editar-correo", "PUT cambia el correo de editable.qa.", tipo="editar", modo="correo"))
    backend.append(_caso("Reglas", "editar-rol", "PUT puede asignar rol admin y devolverlo a usuario.", tipo="editar", modo="rol"))
    backend.append(_caso("Reglas", "editar-sin-clave", "PUT sin clave nueva conserva el acceso anterior.", tipo="editar", modo="sin_clave"))
    backend.append(_caso("Reglas", "editar-clave", "PUT con clave nueva invalida la anterior.", tipo="editar", modo="clave"))
    backend.append(_caso("Reglas", "desactivar-impide-login", "Un usuario inactivo no inicia sesión.", tipo="editar", modo="inactivo"))
    backend.append(_caso("Reglas", "correo-a-minusculas", "El correo se guarda en minúsculas.", tipo="normaliza", modo="correo"))
    backend.append(_caso("Reglas", "usuario-sin-espacios-extremos", "El usuario se guarda sin espacios extremos.", tipo="normaliza", modo="usuario"))
    backend.append(_caso("Reglas", "borrar-y-consultar", "Después de eliminar temporal.baja, GET responde 404.", tipo="borrar_temporal"))
    backend.append(_caso("Reglas", "listado-orden-id", "El listado viene ordenado por id.", tipo="orden"))
    backend.append(_caso("Reglas", "alta-minima-8", "Una clave de exactamente 8 caracteres es válida.", tipo="clave_ocho"))

    for frase in FRASES_LOGIN:
        frontend.append(_caso("Pantalla de acceso", f"login-muestra-{_slug(frase)}", f"La pantalla de acceso muestra «{frase}».", tipo="contiene", donde="login", texto=frase))
    frontend.append(_caso("Pantalla de acceso", "titulo-documento", "El título del documento es Gestión de usuarios.", tipo="igual", donde="titulo", texto="Gestión de usuarios"))
    frontend.append(_caso("Pantalla de acceso", "un-campo-usuario", "Hay un campo de usuario.", tipo="cuenta", donde="inputs_usuario", n=1))
    frontend.append(_caso("Pantalla de acceso", "un-campo-clave", "Hay un campo de clave.", tipo="cuenta", donde="inputs_clave", n=1))
    frontend.append(_caso("Pantalla de acceso", "boton-entrar", "El botón de envío dice Entrar.", tipo="igual", donde="boton_login", texto="Entrar"))
    for frase in AUSENTES_EN_LOGIN:
        frontend.append(_caso("Pantalla de acceso", f"login-no-muestra-{_slug(frase)}", f"La pantalla de acceso no muestra «{frase}».", tipo="ausente", donde="login", texto=frase))
    frontend.append(_caso("Pantalla de acceso", "error-clave-exacto", "La clave incorrecta muestra el mensaje exacto.", tipo="igual", donde="error", texto="Usuario o clave incorrectos."))
    frontend.append(_caso("Pantalla de acceso", "error-no-vacio", "El rechazo de acceso no queda en blanco.", tipo="contiene", donde="error", texto="incorrectos"))

    for encabezado in ENCABEZADOS:
        frontend.append(_caso("Listado", f"encabezado-{_slug(encabezado)}", f"La tabla muestra la columna {encabezado}.", tipo="contiene", donde="tablero", texto=encabezado))
    for boton in BOTONES_LISTA:
        frontend.append(_caso("Listado", f"boton-{_slug(boton)}", f"El listado muestra el botón {boton}.", tipo="contiene", donde="tablero", texto=boton))
    for texto in ("Sesión de admin", "admin@uteq.edu.mx", "activo", "Usuarios"):
        frontend.append(_caso("Listado", f"listado-{_slug(texto)}", f"El listado muestra «{texto}».", tipo="contiene", donde="tablero", texto=texto))
    frontend.append(_caso("Listado", "fila-admin", "La fila del administrador está en la tabla.", tipo="contiene", donde="tablero", texto="admin"))

    for frase in FRASES_FORMULARIO:
        frontend.append(_caso("Formulario", f"formulario-{_slug(frase)}", f"El formulario de alta muestra «{frase}».", tipo="contiene", donde="formulario", texto=frase))
    frontend.append(_caso("Formulario", "clave-obligatoria-en-alta", "El alta pide la clave.", tipo="contiene", donde="formulario", texto="Clave"))

    frontend.append(_caso("CRUD visual", "aviso-creado", "Al guardar, el aviso dice que el usuario fue creado.", tipo="contiene", donde="aviso_creado", texto="Usuario creado."))
    frontend.append(_caso("CRUD visual", "fila-pantalla-demo", "La fila nueva muestra pantalla.demo.", tipo="contiene", donde="tras_crear", texto="pantalla.demo"))
    frontend.append(_caso("CRUD visual", "fila-correo-demo", "La fila nueva muestra el correo de pantalla.demo.", tipo="contiene", donde="tras_crear", texto="pantalla.demo@uteq.edu.mx"))
    frontend.append(_caso("CRUD visual", "aviso-editado", "Al editar, el aviso dice que el usuario fue actualizado.", tipo="contiene", donde="aviso_editado", texto="Usuario actualizado."))
    frontend.append(_caso("CRUD visual", "fila-nombre-nuevo", "La fila editada muestra pantalla.demox.", tipo="contiene", donde="tras_editar", texto="pantalla.demox"))
    frontend.append(_caso("CRUD visual", "ya-no-esta-el-nombre-anterior", "El nombre anterior ya no está después de editar.", tipo="ausente", donde="tras_editar", texto="pantalla.demo@"))
    frontend.append(_caso("CRUD visual", "aviso-eliminado", "Al eliminar, el aviso confirma la baja.", tipo="contiene", donde="aviso_eliminado", texto="Usuario eliminado."))
    frontend.append(_caso("CRUD visual", "fila-ya-no-esta", "La fila eliminada desaparece.", tipo="ausente", donde="tras_eliminar", texto="pantalla.demox"))
    frontend.append(_caso("CRUD visual", "salida-muestra-login", "Al salir vuelve el formulario de acceso.", tipo="contiene", donde="salida", texto="Iniciar sesión"))
    frontend.append(_caso("CRUD visual", "salida-oculta-listado", "Al salir ya no se ofrece Nuevo usuario.", tipo="ausente", donde="salida", texto="Nuevo usuario"))
    frontend.append(_caso("CRUD visual", "sigue-operativo", "El indicador permanece en operativo.", tipo="igual", donde="estado", texto="operativo"))
    frontend.append(_caso("Listado", "ids-en-orden", "Los id de la tabla van de menor a mayor.", tipo="orden_visual"))
    frontend.append(_caso(
        "Reglas visuales", "no-borra-admin-en-pantalla",
        "Eliminar al administrador muestra que no puede borrar su propia cuenta y la fila sigue.",
        tipo="admin_sigue",
    ))

    for usuario, correo, rol, estado in CUENTAS_PANTALLA:
        activo = "true" if estado == "activo" else "false"
        for campo, esperado, detalle in (
            ("usuario", usuario, f"La fila de {usuario} muestra ese nombre."),
            ("correo", correo, f"La fila de {usuario} muestra {correo}."),
            ("rol", rol, f"La fila de {usuario} muestra el rol {rol}."),
            ("estado", estado, f"La fila de {usuario} muestra el estado {estado}."),
            ("id", None, f"El id visible de {usuario} es el mismo que devolvió el API."),
            ("editar", True, f"La fila de {usuario} tiene el botón Editar."),
            ("eliminar", True, f"La fila de {usuario} tiene el botón Eliminar."),
        ):
            frontend.append(_caso("Fila", f"fila-{usuario}-{campo}", detalle, tipo="fila", usuario=usuario, campo=campo, esperado=esperado))
        for campo, esperado, detalle in (
            ("usuario", usuario, f"Al editar {usuario}, el campo trae ese nombre."),
            ("correo", correo, f"Al editar {usuario}, el campo trae {correo}."),
            ("rol", rol, f"Al editar {usuario}, el rol seleccionado es {rol}."),
            ("activo", activo, f"Al editar {usuario}, el estado seleccionado es {estado}."),
            ("titulo", "Editar usuario", f"Al editar {usuario}, el título del formulario es Editar usuario."),
            ("clave", "Nueva clave (opcional)", f"Al editar {usuario}, la clave se pide como opcional."),
        ):
            frontend.append(_caso("Edición", f"edicion-{usuario}-{campo}", detalle, tipo="edicion", usuario=usuario, campo=campo, esperado=esperado))

    for indice, usuario in enumerate(USUARIOS_INVALIDOS, start=1):
        frontend.append(_caso(
            "Rechazo visual", f"pantalla-usuario-{indice:02d}-{_slug(usuario)}",
            f"El alta en pantalla rechaza el usuario «{usuario or 'vacío'}».",
            tipo="ui_rechazo", campo="usuario", valor=usuario,
            mensaje="" if usuario == "" else MENSAJE_USUARIO,
        ))
    for indice, clave in enumerate(CLAVES_INVALIDAS + CLAVES_LIMITE, start=1):
        frontend.append(_caso(
            "Rechazo visual", f"pantalla-clave-{indice:02d}-{len(clave)}",
            f"El alta en pantalla rechaza la clave de {len(clave)} caracteres.",
            tipo="ui_rechazo", campo="clave", valor=clave,
            mensaje="" if clave == "" else MENSAJE_CLAVE,
        ))

    casos = backend + frontend
    ids = [caso["id"] for caso in casos]
    if len(backend) < 700:
        raise RuntimeError(f"El catálogo de backend tiene {len(backend)} pruebas; se pidieron 700.")
    if len(frontend) < 700:
        raise RuntimeError(f"El catálogo de pantalla tiene {len(frontend)} pruebas; se pidieron 700.")
    conteo = {}
    for identificador in ids:
        conteo[identificador] = conteo.get(identificador, 0) + 1
    repetidos = [identificador for identificador, veces in conteo.items() if veces > 1]
    if repetidos:
        raise RuntimeError(f"Hay identificadores repetidos: {repetidos}")
    return backend, frontend


def _slug(texto):
    limpio = "".join(caracter if caracter.isalnum() else "-" for caracter in str(texto).lower())
    limpio = "-".join(parte for parte in limpio.split("-") if parte)
    return (limpio or "vacio")[:48]


BACKEND, FRONTEND = construir()
