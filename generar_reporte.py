# -*- coding: utf-8 -*-
"""Reporte institucional del proyecto parcial 2."""
import json
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

RAIZ = Path(__file__).resolve().parent
EVIDENCIAS = RAIZ / "evidencias"
RESULTADOS = EVIDENCIAS / "resultados.json"
LOGO = RAIZ / "logo-uteq.png"
DOCX = RAIZ / "Reporte-Proyecto-Parcial-2.docx"

NAVY = "0F172A"
VERDE = "0E6B4C"
SLATE = "334155"
LIGHT = "F1F5F9"
GREEN = "166534"
GREEN_BG = "DCFCE7"
RED = "991B1B"
RED_BG = "FEE2E2"
WHITE = "FFFFFF"
ANCHO = 10080

FIGURAS = [
    ("01_login.png", "Pantalla de inicio de sesión. El indicador operativo confirma que /salud responde bien."),
    ("02_login_invalido.png", "Intento con clave incorrecta. La interfaz muestra el rechazo sin abrir el listado."),
    ("03_listado.png", "CRUD de usuarios después de autenticarse como administrador."),
    ("04_alta.png", "Formulario de alta con usuario, correo, rol y clave."),
    ("05_creado.png", "El usuario nuevo aparece en la tabla."),
    ("06_editado.png", "El mismo registro después de cambiar el nombre."),
    ("07_eliminado.png", "La fila desaparece al confirmar la eliminación."),
    ("08_salida.png", "Cierre de sesión: vuelve el formulario de acceso."),
    ("09_fallo_intencional.png", "Con FORZAR_FALLO=1 el indicador pasa a fallo intencional y /salud responde 503."),
]


def fuente(run, tamano=12, negrita=False, cursiva=False, color=NAVY):
    run.font.name = "Times New Roman"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
    run.font.size = Pt(tamano)
    run.bold = negrita
    run.italic = cursiva
    run.font.color.rgb = RGBColor.from_string(color)


def alinear(valor):
    return {
        "centro": WD_ALIGN_PARAGRAPH.CENTER,
        "izquierda": WD_ALIGN_PARAGRAPH.LEFT,
        "justificar": WD_ALIGN_PARAGRAPH.JUSTIFY,
    }[valor]


def parrafo(doc, texto, tamano=12, negrita=False, cursiva=False, alineacion="justificar", antes=0, despues=8, color=NAVY):
    bloque = doc.add_paragraph()
    bloque.alignment = alinear(alineacion)
    bloque.paragraph_format.space_before = Pt(antes)
    bloque.paragraph_format.space_after = Pt(despues)
    bloque.paragraph_format.line_spacing = 1.15
    run = bloque.add_run(texto)
    fuente(run, tamano, negrita, cursiva, color)
    return bloque


def sombrear(celda, color):
    tc_pr = celda._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), color)
    tc_pr.append(shd)


def margenes_celda(celda):
    tc_pr = celda._tc.get_or_add_tcPr()
    tc_mar = OxmlElement("w:tcMar")
    for lado, valor in (("top", 40), ("left", 60), ("bottom", 40), ("right", 60)):
        nodo = OxmlElement(f"w:{lado}")
        nodo.set(qn("w:w"), str(valor))
        nodo.set(qn("w:type"), "dxa")
        tc_mar.append(nodo)
    tc_pr.append(tc_mar)


def bordes(tabla, color="CBD5E1", grosor="4"):
    marco = OxmlElement("w:tblBorders")
    for lado in ("top", "left", "bottom", "right", "insideH", "insideV"):
        nodo = OxmlElement(f"w:{lado}")
        nodo.set(qn("w:val"), "single")
        nodo.set(qn("w:sz"), grosor)
        nodo.set(qn("w:space"), "0")
        nodo.set(qn("w:color"), color)
        marco.append(nodo)
    tabla._tbl.tblPr.append(marco)


def ancho_tabla(tabla, anchos):
    tabla.autofit = False
    tabla.allow_autofit = False
    tbl_w = tabla._tbl.tblPr.find(qn("w:tblW"))
    if tbl_w is None:
        tbl_w = OxmlElement("w:tblW")
        tabla._tbl.tblPr.append(tbl_w)
    tbl_w.set(qn("w:w"), str(sum(anchos)))
    tbl_w.set(qn("w:type"), "dxa")
    grid = tabla._tbl.find(qn("w:tblGrid"))
    for hijo in list(grid):
        grid.remove(hijo)
    for ancho in anchos:
        col = OxmlElement("w:gridCol")
        col.set(qn("w:w"), str(ancho))
        grid.append(col)
    for fila in tabla.rows:
        for indice, celda in enumerate(fila.cells):
            tc_pr = celda._tc.get_or_add_tcPr()
            tc_w = tc_pr.find(qn("w:tcW"))
            if tc_w is None:
                tc_w = OxmlElement("w:tcW")
                tc_pr.append(tc_w)
            tc_w.set(qn("w:w"), str(anchos[indice]))
            tc_w.set(qn("w:type"), "dxa")


def texto_celda(celda, texto, tamano=11, negrita=False, color=NAVY, alineacion="izquierda", fondo=None):
    celda.text = ""
    bloque = celda.paragraphs[0]
    bloque.alignment = alinear(alineacion)
    bloque.paragraph_format.space_before = Pt(0)
    bloque.paragraph_format.space_after = Pt(0)
    run = bloque.add_run(str(texto))
    fuente(run, tamano, negrita, False, color)
    margenes_celda(celda)
    if fondo:
        sombrear(celda, fondo)


def ficha(doc, filas):
    tabla = doc.add_table(rows=len(filas), cols=2)
    ancho_tabla(tabla, [2800, 7280])
    bordes(tabla)
    for indice, (etiqueta, valor) in enumerate(filas):
        texto_celda(tabla.cell(indice, 0), etiqueta, negrita=True, fondo=LIGHT)
        texto_celda(tabla.cell(indice, 1), valor)
    return tabla


def construir(datos):
    pruebas = datos.get("pruebas") or []
    correctas = sum(1 for caso in pruebas if caso["estado"] == "CORRECTO")
    fallidas = len(pruebas) - correctas
    fecha = datos.get("fecha", "20 de noviembre de 2026")

    doc = Document()
    normal = doc.styles["Normal"]
    normal.font.name = "Times New Roman"
    normal.font.size = Pt(12)
    normal.element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
    seccion = doc.sections[0]
    seccion.page_width = Inches(8.5)
    seccion.page_height = Inches(11)
    seccion.left_margin = Inches(0.85)
    seccion.right_margin = Inches(0.85)
    seccion.top_margin = Inches(0.8)
    seccion.bottom_margin = Inches(0.75)
    doc.core_properties.title = "Proyecto parcial 2. CI/CD, pruebas y observabilidad"
    doc.core_properties.author = "Bruno Jesús Caldera Landa"
    doc.core_properties.subject = "Gestión del Proceso de Desarrollo de Software"

    if LOGO.exists():
        logo = doc.add_paragraph()
        logo.alignment = WD_ALIGN_PARAGRAPH.CENTER
        logo.add_run().add_picture(str(LOGO), width=Inches(2.6))

    banner = doc.add_table(rows=1, cols=1)
    ancho_tabla(banner, [ANCHO])
    bordes(banner, NAVY, "0")
    celda = banner.cell(0, 0)
    sombrear(celda, NAVY)
    lineas = (
        ("UNIVERSIDAD TECNOLÓGICA DE QUERÉTARO", 15, True, 8, 2),
        ("Organismo público descentralizado del Gobierno del Estado de Querétaro", 10, False, 0, 0),
        ("División de Tecnologías de la Información", 10, False, 0, 6),
    )
    for indice, (texto, tamano, negrita, antes, despues) in enumerate(lineas):
        bloque = celda.paragraphs[0] if indice == 0 else celda.add_paragraph()
        bloque.alignment = WD_ALIGN_PARAGRAPH.CENTER
        bloque.paragraph_format.space_before = Pt(antes)
        bloque.paragraph_format.space_after = Pt(despues)
        run = bloque.add_run(texto)
        fuente(run, tamano, negrita, False, WHITE)

    parrafo(doc, "PROYECTO PARCIAL 2", 12, True, False, "centro", antes=14, despues=4, color=VERDE)
    parrafo(doc, "Arquitectura de entrega continua, pruebas automatizadas y observabilidad", 16, True, False, "centro", antes=0, despues=6)
    parrafo(doc, "Login, CRUD de usuarios, Playwright, GitHub Actions, AWS EC2 y OpenObserve", 11, False, True, "centro", antes=0, despues=10, color=SLATE)
    ficha(doc, [
        ("Estudiante", "Bruno Jesús Caldera Landa"),
        ("Matrícula", "2023371132"),
        ("Programa", "Ingeniería en Desarrollo y Gestión de Software"),
        ("Asignatura", "Gestión del Proceso de Desarrollo de Software"),
        ("Docente", "Emmanuel Martínez Hernández"),
        ("Lugar y fecha", f"Querétaro, {fecha}"),
    ])

    doc.add_page_break()
    parrafo(doc, "1. Introducción", 16, True, False, "izquierda", antes=0, despues=8)
    parrafo(doc, "El objetivo del proyecto es entregar un sistema con inicio de sesión y CRUD de usuarios dentro de un flujo de integración y despliegue continuo. GitHub Actions ejecuta la suite de extremo a extremo y solo entonces abre una sesión SSH hacia una instancia de AWS EC2 para reemplazar los contenedores. Cada ejecución, exitosa o fallida, y cada despliegue se registran en OpenObserve. La aplicación desplegada envía logs, métricas y trazas con OpenTelemetry, y un agente del servidor publica CPU, memoria RAM, ancho de banda y temperatura.")
    parrafo(doc, "El sistema se revisa en clase. Cada omisión de un requerimiento resta cuatro puntos, por lo que este documento recorre los requerimientos funcionales, los tres criterios de aceptación y las evidencias de la suite. Las direcciones del repositorio y del servidor quedan indicadas para completarlas con los valores reales de la cuenta de GitHub y de la instancia, porque esas dos piezas viven fuera de este equipo.")

    parrafo(doc, "2. Requerimientos y criterios de aceptación", 16, True, False, "izquierda", antes=12, despues=8)
    parrafo(doc, "La especificación pide seis requerimientos. La tabla siguiente dice dónde quedó cada uno en el repositorio.")
    filas_rf = [
        ("RF-01", "Pruebas de frontend y backend con Playwright", "tests/test_ui.py y tests/test_api.py"),
        ("RF-02", "Despliegue solo si la suite pasa", ".github/workflows/cicd.yml, job desplegar"),
        ("RF-03", "Resultado de pruebas y de despliegue en OpenObserve", "observabilidad/publicar_evento.py"),
        ("RF-04", "Logs, métricas y trazas OTLP de la aplicación", "app/telemetria.py y app/main.py"),
        ("RF-05", "CPU, RAM, ancho de banda y temperatura", "observabilidad/agente_host.py"),
        ("RF-06", "Tablero y alerta operativa", "observabilidad/tablero.json e importar_tablero.py"),
    ]
    tabla = doc.add_table(rows=1, cols=3)
    ancho_tabla(tabla, [1200, 4680, 4200])
    bordes(tabla)
    for indice, titulo in enumerate(("ID", "Requerimiento", "Dónde está")):
        texto_celda(tabla.rows[0].cells[indice], titulo, tamano=10, negrita=True, color=WHITE, fondo=NAVY)
    for rf, texto, lugar in filas_rf:
        fila = tabla.add_row()
        texto_celda(fila.cells[0], rf, tamano=10, negrita=True)
        texto_celda(fila.cells[1], texto, tamano=10)
        texto_celda(fila.cells[2], lugar, tamano=10)
    parrafo(doc, "Criterio 1. Un commit con FORZAR_FALLO=1 hace que /salud responda 503 y que la pantalla muestre el texto «fallo intencional». Las pruebas de API y de interfaz esperan el estado operativo, así que Playwright falla. El job registrar envía el incidente a OpenObserve y el job desplegar no arranca: no hay conexión SSH.", antes=10)
    parrafo(doc, "Criterio 2. Un commit válido deja la suite en verde. El workflow actualiza los contenedores con deploy/actualizar.sh y después publica el evento de despliegue completado.")
    parrafo(doc, "Criterio 3. En OpenObserve conviven el stream cicd (ejecuciones del pipeline), las trazas de cada petición HTTP y las series del agente: host_cpu_utilization, host_memory_utilization, host_network_receive_bytes_per_second y host_temperature_celsius. La temperatura solo tiene puntos cuando el sistema expone un sensor; en muchas EC2 el hipervisor no publica zonas térmicas y el agente deja constancia de esa ausencia sin inventar una lectura.")

    parrafo(doc, "3. Arquitectura", 16, True, False, "izquierda", antes=12, despues=8)
    parrafo(doc, "La aplicación es un servicio FastAPI. La interfaz es una página con el formulario de acceso y la tabla de usuarios. La sesión viaja en una cookie firmada. Las contraseñas se guardan con PBKDF2-HMAC-SHA256 y la base es SQLite. Al arrancar, si no hay cuentas, se crea el administrador.")
    parrafo(doc, "En la EC2, Docker Compose levanta tres servicios: OpenObserve en el puerto 5080, la aplicación en el 8080 y el agente de host con el perfil servidor. El agente lee /proc y /sys de la instancia. La aplicación y el agente exportan OTLP por HTTP hacia http://openobserve:5080/api/default, con autenticación básica. GitHub Actions no despliega la imagen por sí mismo: entra por SSH y reconstruye esa pila. El puerto 80 queda libre para otros trabajos de la misma instancia.")
    parrafo(doc, "Las métricas de la aplicación son http_requests_total, http_errors_total y http_request_duration_seconds, con método, ruta, código de estado y marca de tiempo. Cada consulta SQLite abre un tramo de traza db.query. Los logs de login, alta, edición, baja y excepciones salen en JSON por el mismo exportador.")

    parrafo(doc, "4. Aplicación: login y CRUD", 16, True, False, "izquierda", antes=12, despues=8)
    parrafo(doc, "El administrador inicia sesión, lista usuarios, crea, edita y elimina. Una cuenta con rol usuario puede autenticarse y recibe 403 si intenta el CRUD. No se puede borrar la propia sesión ni dejar el sistema sin un administrador activo. La clave no sale en ninguna respuesta.")
    parrafo(doc, "Las figuras siguientes salen de la misma corrida de Playwright que produce la sección 5.")
    numero = 1
    for archivo, pie in FIGURAS:
        ruta = EVIDENCIAS / archivo
        if not ruta.exists():
            continue
        parrafo(doc, f"Figura {numero}. {pie}", 11, True, False, "centro", antes=8, despues=4)
        foto = doc.add_paragraph()
        foto.alignment = WD_ALIGN_PARAGRAPH.CENTER
        foto.add_run().add_picture(str(ruta), width=Inches(6.1))
        numero += 1
    if numero == 1:
        parrafo(doc, "Aún no hay capturas en evidencias. Ejecute pytest y vuelva a generar este documento.")

    parrafo(doc, "5. Pruebas automatizadas", 16, True, False, "izquierda", antes=12, despues=8)
    if pruebas:
        parrafo(doc, f"La corrida local usó Python {datos.get('python', '')} y terminó con {correctas} pruebas correctas y {fallidas} fallidas, en {datos.get('duracion_s', 0)} segundos. El backend usa el cliente HTTP de Playwright contra el servidor real. El frontend usa Chromium. tests/test_fallo.py levanta otra instancia con el fallo intencional y comprueba el 503 y el texto de la pantalla; esa prueba debe pasar en la suite normal.")
        resumen = doc.add_table(rows=1, cols=4)
        ancho_tabla(resumen, [5200, 1620, 1620, 1640])
        bordes(resumen)
        for indice, titulo in enumerate(("Prueba", "Estado", "Segundos", "Archivo")):
            texto_celda(resumen.rows[0].cells[indice], titulo, tamano=10, negrita=True, color=WHITE, fondo=NAVY)
        for caso in pruebas:
            fila = resumen.add_row()
            ok = caso["estado"] == "CORRECTO"
            texto_celda(fila.cells[0], caso["nombre"], tamano=9)
            texto_celda(fila.cells[1], caso["estado"], tamano=9, negrita=True, color=GREEN if ok else RED, fondo=GREEN_BG if ok else RED_BG, alineacion="centro")
            texto_celda(fila.cells[2], str(caso["duracion_s"]), tamano=9, alineacion="centro")
            texto_celda(fila.cells[3], caso["nodo"].split("::")[0].replace("tests/", ""), tamano=8)
    else:
        parrafo(doc, "No se encontró evidencias/resultados.json. Ejecute pytest antes de regenerar el reporte.")

    parrafo(doc, "6. Pipeline y despliegue condicionado", 16, True, False, "izquierda", antes=12, despues=8)
    parrafo(doc, "El workflow tiene tres jobs. pruebas instala Playwright y corre pytest. registrar publica el resultado en el stream cicd de OpenObserve, tanto si la suite pasó como si falló. desplegar solo existe cuando los dos anteriores tuvieron éxito, el evento es un push y la rama es main. En ese caso appleboy/ssh-action ejecuta git reset y deploy/actualizar.sh. Si el health check de /salud no responde, el script sale con error y el workflow registra un despliegue fallido. Un pull request corre pruebas y registro, y no toca la EC2.")
    parrafo(doc, "Antes del primer push hay que levantar la pila a mano en la instancia, porque el runner de GitHub tiene que alcanzar OpenObserve para registrar incluso el fallo. El security group debe abrir 22, 8080 y 5080. La guía de secrets, del bootstrap y del fallo intencional está en el README del repositorio.")

    parrafo(doc, "7. Repositorio, servidor y credenciales", 16, True, False, "izquierda", antes=12, despues=8)
    parrafo(doc, "El repositorio público es https://github.com/Brunne-CL/Proyecto-Parcial-2 y la instancia es 54.227.162.119. La aplicación queda en el puerto 8080 y OpenObserve en el 5080.")
    ficha(doc, [
        ("Repositorio", "https://github.com/Brunne-CL/Proyecto-Parcial-2"),
        ("Aplicación", "http://54.227.162.119:8080"),
        ("Salud", "http://54.227.162.119:8080/salud"),
        ("OpenObserve", "http://54.227.162.119:5080"),
        ("Usuario de la aplicación", "admin"),
        ("Clave de la aplicación", "Admin123!"),
        ("Correo del administrador", "admin@uteq.edu.mx"),
        ("Usuario de OpenObserve", "admin@uteq.edu.mx"),
        ("Clave de OpenObserve", "Gestion2026!"),
        ("Organización OpenObserve", "default"),
    ])
    parrafo(doc, "Esas claves son las de demostración definidas en .env.example. En el servidor conviene cambiar SECRET_KEY. No forman parte del historial de Git: el archivo .env está ignorado.", antes=8)

    parrafo(doc, "8. Conclusiones", 16, True, False, "izquierda", antes=12, despues=8)
    if fallidas == 0 and pruebas:
        parrafo(doc, f"La suite local cerró {len(pruebas)} pruebas en estado correcto, cubriendo acceso, CRUD, autorización, validaciones y el modo de fallo que bloquea el despliegue. El pipeline queda armado para no abrir SSH cuando Playwright falla y para registrar ambos resultados en OpenObserve.")
    elif pruebas:
        parrafo(doc, f"La corrida dejó {fallidas} pruebas en fallo. Hay que corregirlas antes de entregar: un push a main con la suite en rojo no despliega, y además registra el incidente.")
    else:
        parrafo(doc, "Falta la evidencia de la suite. Regenere el reporte después de pytest.")
    parrafo(doc, "La observabilidad queda lista para la revisión en clase cuando la EC2 esté en marcha: tablero de pipeline, trazas de las peticiones y gráficas de CPU, memoria, ancho de banda y temperatura. Si la instancia no expone sensor térmico, la gráfica de temperatura permanece vacía y el agente informa host_temperature_available en cero; CPU, RAM y red sí se publican.")

    parrafo(doc, "9. Fuentes de información", 16, True, False, "izquierda", antes=12, despues=8)
    for texto in (
        "Microsoft. (2026). Playwright. https://playwright.dev/python/",
        "OpenObserve. (2026). OpenTelemetry ingestion. https://openobserve.ai/docs/ingestion/traces/",
        "OpenTelemetry. (2026). Python SDK. https://opentelemetry.io/docs/languages/python/",
        "GitHub. (2026). GitHub Actions. https://docs.github.com/actions",
        "Amazon Web Services. (2026). Amazon EC2. https://docs.aws.amazon.com/ec2/",
    ):
        parrafo(doc, texto, 11, False, False, "izquierda", antes=0, despues=4)
    return doc


def main():
    datos = {}
    if RESULTADOS.exists():
        datos = json.loads(RESULTADOS.read_text(encoding="utf-8"))
    documento = construir(datos)
    documento.save(DOCX)
    print(DOCX)


if __name__ == "__main__":
    main()
