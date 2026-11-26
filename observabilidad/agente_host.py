"""Métricas de CPU, memoria, ancho de banda y temperatura hacia OpenObserve."""
import os
import socket
import time
from pathlib import Path

import psutil
from opentelemetry.metrics import Observation

from app.telemetria import configurar

ESTADO = {}
ANFITRION = socket.gethostname()


def _observar(clave):
    def callback(_opciones):
        if clave in ESTADO and ESTADO[clave] is not None:
            yield Observation(ESTADO[clave], {"host.name": ANFITRION})

    return callback


def _temperatura_psutil():
    try:
        sensores = psutil.sensors_temperatures() or {}
    except Exception:
        return None
    lecturas = []
    for entradas in sensores.values():
        for entrada in entradas:
            if entrada.current is not None:
                lecturas.append(float(entrada.current))
    if not lecturas:
        return None
    return sum(lecturas) / len(lecturas)


def _temperatura_sys(sysfs):
    base = Path(sysfs)
    lecturas = []
    termicos = base / "class" / "thermal"
    if termicos.exists():
        for archivo in termicos.glob("thermal_zone*/temp"):
            try:
                lecturas.append(int(archivo.read_text().strip()) / 1000)
            except (OSError, ValueError):
                continue
    hwmon = base / "class" / "hwmon"
    if hwmon.exists():
        for archivo in hwmon.glob("hwmon*/temp*_input"):
            try:
                lecturas.append(int(archivo.read_text().strip()) / 1000)
            except (OSError, ValueError):
                continue
    if not lecturas:
        return None
    return sum(lecturas) / len(lecturas)


def _muestra_proc(proc, sysfs, anterior):
    stat = (Path(proc) / "stat").read_text(encoding="utf-8").splitlines()[0].split()[1:8]
    numeros = [int(parte) for parte in stat]
    time.sleep(1)
    stat2 = (Path(proc) / "stat").read_text(encoding="utf-8").splitlines()[0].split()[1:8]
    numeros2 = [int(parte) for parte in stat2]
    total = sum(numeros2) - sum(numeros)
    inactivo = (numeros2[3] + numeros2[4]) - (numeros[3] + numeros[4])
    cpu = 0 if total <= 0 else (1 - inactivo / total) * 100

    memoria = {}
    for linea in (Path(proc) / "meminfo").read_text(encoding="utf-8").splitlines():
        nombre, valor = linea.split(":", 1)
        memoria[nombre] = int(valor.strip().split()[0]) * 1024
    usada = memoria["MemTotal"] - memoria.get("MemAvailable", memoria["MemFree"])
    porcentaje = usada / memoria["MemTotal"] * 100 if memoria["MemTotal"] else 0

    rx = tx = 0
    for linea in (Path(proc) / "net" / "dev").read_text(encoding="utf-8").splitlines()[2:]:
        iface, resto = linea.split(":", 1)
        if iface.strip() == "lo":
            continue
        columnas = resto.split()
        rx += int(columnas[0])
        tx += int(columnas[8])
    ahora = time.time()
    rx_s = tx_s = 0.0
    if anterior and ahora > anterior["t"]:
        delta = ahora - anterior["t"]
        rx_s = max(0, (rx - anterior["rx"]) / delta)
        tx_s = max(0, (tx - anterior["tx"]) / delta)
    return {
        "cpu": cpu,
        "mem_bytes": usada,
        "mem_pct": porcentaje,
        "rx": rx_s,
        "tx": tx_s,
        "temp": _temperatura_sys(sysfs) if sysfs else _temperatura_psutil(),
        "anterior": {"t": ahora, "rx": rx, "tx": tx},
    }


def _muestra_psutil(anterior):
    cpu = psutil.cpu_percent(interval=1)
    memoria = psutil.virtual_memory()
    red = psutil.net_io_counters()
    ahora = time.time()
    rx_s = tx_s = 0.0
    if anterior and ahora > anterior["t"]:
        delta = ahora - anterior["t"]
        rx_s = max(0, (red.bytes_recv - anterior["rx"]) / delta)
        tx_s = max(0, (red.bytes_sent - anterior["tx"]) / delta)
    return {
        "cpu": cpu,
        "mem_bytes": memoria.used,
        "mem_pct": memoria.percent,
        "rx": rx_s,
        "tx": tx_s,
        "temp": _temperatura_psutil(),
        "anterior": {"t": ahora, "rx": red.bytes_recv, "tx": red.bytes_sent},
    }


def main():
    medidor, _ = configurar()
    medidor.create_observable_gauge("host_cpu_utilization", callbacks=[_observar("cpu")], unit="%", description="Uso de CPU")
    medidor.create_observable_gauge("host_memory_usage_bytes", callbacks=[_observar("mem_bytes")], unit="By", description="Memoria RAM en uso")
    medidor.create_observable_gauge("host_memory_utilization", callbacks=[_observar("mem_pct")], unit="%", description="Porcentaje de RAM")
    medidor.create_observable_gauge("host_network_receive_bytes_per_second", callbacks=[_observar("rx")], unit="By/s", description="Ancho de banda de entrada")
    medidor.create_observable_gauge("host_network_transmit_bytes_per_second", callbacks=[_observar("tx")], unit="By/s", description="Ancho de banda de salida")
    medidor.create_observable_gauge("host_temperature_celsius", callbacks=[_observar("temp")], unit="Cel", description="Temperatura del equipo")
    medidor.create_observable_gauge("host_temperature_available", callbacks=[_observar("temp_ok")], description="1 si hay sensor de temperatura")

    proc = os.environ.get("HOST_PROC", "").strip()
    sysfs = os.environ.get("HOST_SYS", "").strip()
    anterior = None
    aviso_temperatura = False
    while True:
        muestra = _muestra_proc(proc, sysfs, anterior) if proc else _muestra_psutil(anterior)
        anterior = muestra.pop("anterior")
        ESTADO.update(muestra)
        ESTADO["temp_ok"] = 0 if muestra["temp"] is None else 1
        if muestra["temp"] is None:
            ESTADO.pop("temp", None)
            if not aviso_temperatura:
                print("Temperatura no disponible en este equipo. CPU, RAM y red sí se publican.", flush=True)
                aviso_temperatura = True
        print(
            f"cpu={muestra['cpu']:.1f}% ram={muestra['mem_pct']:.1f}% "
            f"rx={muestra['rx']:.0f}B/s tx={muestra['tx']:.0f}B/s temp={muestra['temp']}",
            flush=True,
        )
        time.sleep(15)


if __name__ == "__main__":
    main()
