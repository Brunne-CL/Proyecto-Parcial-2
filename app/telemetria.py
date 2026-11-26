"""Exportación OpenTelemetry hacia OpenObserve: trazas, métricas y logs."""
import atexit
import base64
import logging
import os

from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

_proveedores = []


def encabezados():
    usuario = os.environ.get("OO_USER", "").strip()
    clave = os.environ.get("OO_PASSWORD", "").strip()
    if usuario and clave:
        token = base64.b64encode(f"{usuario}:{clave}".encode("utf-8")).decode("ascii")
        return {"Authorization": f"Basic {token}"}
    crudo = os.environ.get("OTEL_EXPORTER_OTLP_HEADERS", "").strip()
    resultado = {}
    for parte in crudo.split(","):
        if "=" not in parte:
            continue
        nombre, valor = parte.split("=", 1)
        resultado[nombre.strip()] = valor.strip().replace("%20", " ")
    return resultado


def configurar():
    punto = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "").strip().rstrip("/")
    servicio = os.environ.get("OTEL_SERVICE_NAME", "gestion-usuarios")
    recurso = Resource.create(
        {
            "service.name": servicio,
            "service.version": "1.0.0",
            "deployment.environment": os.environ.get("ENTORNO", "local"),
        }
    )
    if not punto:
        logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
        return metrics.get_meter(servicio), trace.get_tracer(servicio)

    cabeceras = encabezados()
    trazas = TracerProvider(resource=recurso)
    trazas.add_span_processor(
        BatchSpanProcessor(OTLPSpanExporter(endpoint=f"{punto}/v1/traces", headers=cabeceras))
    )
    trace.set_tracer_provider(trazas)

    lector = PeriodicExportingMetricReader(
        OTLPMetricExporter(endpoint=f"{punto}/v1/metrics", headers=cabeceras),
        export_interval_millis=15000,
    )
    medidor_proveedor = MeterProvider(resource=recurso, metric_readers=[lector])
    metrics.set_meter_provider(medidor_proveedor)

    registros = LoggerProvider(resource=recurso)
    registros.add_log_record_processor(
        BatchLogRecordProcessor(OTLPLogExporter(endpoint=f"{punto}/v1/logs", headers=cabeceras))
    )
    manejador = LoggingHandler(level=logging.INFO, logger_provider=registros)
    raiz = logging.getLogger()
    raiz.handlers.clear()
    raiz.addHandler(manejador)
    raiz.addHandler(logging.StreamHandler())
    raiz.setLevel(logging.INFO)

    _proveedores.extend([trazas, medidor_proveedor, registros])

    def cerrar():
        for proveedor in _proveedores:
            proveedor.shutdown()

    atexit.register(cerrar)
    return metrics.get_meter(servicio), trace.get_tracer(servicio)
