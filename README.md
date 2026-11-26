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

1. En cada push o pull request corre Playwright: la API (`tests/test_api.py`) y la pantalla (`tests/test_ui.py`).
2. Publica en OpenObserve el resultado (éxito o fallo), con commit, rama y usuario. Si OpenObserve no recibe el evento, el job falla.
3. Solo si las pruebas y el registro salieron bien, y el push es a `main`, abre SSH a la EC2, reconstruye los contenedores y registra el despliegue. Un fallo de Playwright no llega al paso SSH.

### Secrets

En el repositorio: Settings, Secrets and variables, Actions.

| Secret | Valor |
| --- | --- |
| `OPENOBSERVE_URL` | `http://IP-PUBLICA:5080` |
| `OPENOBSERVE_ORG` | `default` |
| `OO_USER` | `admin@uteq.edu.mx` |
| `OO_PASSWORD` | `Gestion2026!` |
| `EC2_HOST` | IP pública |
| `EC2_USER` | `ec2-user` en Amazon Linux, `ubuntu` en Ubuntu |
| `EC2_SSH_KEY` | Contenido del `.pem` |

El security group necesita 22, 8080 y 5080. El puerto 5080 tiene que ser alcanzable desde GitHub Actions: el runner es quien avisa a OpenObserve cuando las pruebas fallan, y en ese caso no debe haber SSH.

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

Para el criterio de aceptación que bloquea el despliegue, en un commit de prueba ponga `FORZAR_FALLO=1` en el entorno del servidor de pruebas. La forma directa en local es:

```powershell
$env:FORZAR_FALLO = "1"
```

`/salud` responde 503 y la pantalla muestra «fallo intencional». `tests/test_ui.py` y `tests/test_api.py` exigen el estado operativo, así que el workflow falla, registra el incidente y no ejecuta el job de SSH. `tests/test_fallo.py` comprueba que ese modo responde 503; ese caso sí debe pasar en la suite normal.

Quite la variable antes del commit que sí debe desplegarse.
