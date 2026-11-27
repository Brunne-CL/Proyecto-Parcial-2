# Proyecto parcial 2

Sistema con login y CRUD de usuarios, pruebas de frontend y backend con Playwright, pipeline de GitHub Actions que solo actualiza la EC2 cuando la suite pasa, y observabilidad en OpenObserve.

Esta carpeta es la raíz del repositorio. GitHub Actions no ejecuta el workflow si `.github` no está en la raíz.

## Credenciales de demostración

| Sistema | Usuario | Clave | Dirección |
| --- | --- | --- | --- |
| Aplicación | `admin` | `Admin123!` | http://IP:8080 |
| OpenObserve | `admin@uteq.edu.mx` | `Gestion2026!` | http://IP:5080 |

Cambie `SECRET_KEY` en el `.env` del servidor. Las cuentas de arriba son las que pide el reporte.

## Correr en local

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
python -m playwright install chromium
pytest
```

Para ver la interfaz:

```powershell
$env:DATABASE_PATH = "data/usuarios.db"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8080
```

## Pila con OpenObserve

Hace falta Docker.

```powershell
Copy-Item .env.example .env
docker compose up -d --build
```

La aplicación queda en http://127.0.0.1:8080 y OpenObserve en http://127.0.0.1:5080.

En esta máquina, las métricas del equipo se publican con:

```powershell
python -m observabilidad.agente_host
```

En la EC2 las publica el servicio `agente` (perfil `servidor`), leyendo CPU, RAM, red y, si el hipervisor la expone, la temperatura.

Cuando OpenObserve ya responde:

```powershell
python observabilidad/importar_tablero.py
```

Eso crea el stream `cicd`, intenta cargar `observabilidad/tablero.json` y una alerta cuando `estado = fallo`. Si la versión de OpenObserve rechaza el JSON, impórtelo desde Dashboards, Import.

## Qué hace el pipeline

1. En cada push o pull request genera dos reportes HTML en Ubuntu: `reporte-pytest` con las 700 comprobaciones concretas de backend y `reporte-playwright` con las 700 de la interfaz (`tests/test_700.py`). Un tercer job corre `tests/test_alpine.py` dentro de `python:3.12-alpine` y genera `reporte-alpine`.
2. Los tres HTML quedan como artefactos de esa ejecución. En la página del workflow, al final, está la sección Artifacts.
3. Publica en OpenObserve el resultado (éxito o fallo), con commit, rama y usuario. Si OpenObserve no recibe el evento, el job falla.
4. Solo si pytest, Playwright, Alpine y el registro salieron bien, y el push es a `main`, abre SSH a la EC2, reconstruye los contenedores y registra el despliegue. Un fallo no llega al paso SSH.

### Secrets

En el repositorio: Settings, Secrets and variables, Actions.

| Secret | Valor |
| --- | --- |
| `OPENOBSERVE_URL` | `http://54.227.162.119:5080` |
| `OPENOBSERVE_ORG` | `default` |
| `OO_USER` | `admin@uteq.edu.mx` |
| `OO_PASSWORD` | `Gestion2026!` |
| `EC2_HOST` | IP pública |
| `EC2_USER` | `ec2-user` en Amazon Linux, `ubuntu` en Ubuntu |
| `EC2_SSH_KEY` | Contenido del `.pem` |

El security group necesita 22, 8080 y 5080. El puerto 5080 tiene que ser alcanzable desde GitHub Actions: el runner es quien avisa a OpenObserve cuando las pruebas fallan, y en ese caso no debe haber SSH.

Si `OPENOBSERVE_URL` no está en los secrets, el workflow usa `http://54.227.162.119:5080` y el usuario de `.env.example`. `EC2_HOST`, `EC2_USER` y `EC2_SSH_KEY` sí tienen que estar: sin la llave el job de despliegue no puede abrir SSH.

## EC2, una vez

1. Ejecute `deploy/bootstrap-ec2.sh`.
2. Cierre la sesión y vuelva a entrar.
3. Clone este repositorio en `/opt/gestion-usuarios`.
4. `cp .env.example .env` y cambie `SECRET_KEY`.
5. `sudo docker compose --profile servidor up -d --build`
6. Abra http://IP:8080/salud y http://IP:5080.
7. Guarde los secrets y haga push a `main`.

El puerto 80 de la misma instancia puede seguir usándolo el proyecto integrador. Esta aplicación usa el 8080.

## Fallo intencional

Para el criterio de aceptación que bloquea el despliegue, cambie el archivo `fallo_intencional` de `0` a `1` y haga commit. `/salud` responde 503 y la pantalla muestra «fallo intencional». La suite principal exige el estado operativo, así que Playwright falla, el workflow registra el incidente y no abre SSH. `tests/test_fallo.py` sigue pasando: comprueba ese 503 en un servidor aparte.

Vuelva a dejar `fallo_intencional` en `0` antes del commit que sí debe desplegarse. En local también puede forzar el modo con `$env:FORZAR_FALLO = "1"`.
