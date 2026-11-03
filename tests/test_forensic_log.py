"""
Tests para VulcanoEventEngine.

responsable: integrante 6 - Simulación de Caos y Pruebas Forenses

OBJETIVO:
Validar la generación y el contenido de los logs forenses comprimidos en Gzip.
"""

import gzip
import json
import logging
import logging.handlers
import os
from datetime import datetime, timedelta

import pytest

from vulcano_telemetry.logging_engine import setup_vulcano_logging

REQUIRED_FIELDS = {"timestamp", "logger", "level", "message", "process", "threadName"}


@pytest.fixture
def forensic_env(tmp_path):
    """Logger real del engine escribiendo en un directorio temporal."""
    log_file = tmp_path / "vulcano_test.log"
    logger = setup_vulcano_logging(str(log_file))
    listener = logger.listener
    yield logger, listener, log_file

    # Teardown: dejar el logger global limpio para otros tests
    if getattr(listener, "_thread", None):
        listener.stop()
    for handler in listener.handlers:
        handler.close()
    for handler in list(logger.handlers):
        if isinstance(handler, logging.handlers.QueueHandler):
            logger.removeHandler(handler)


def flush_and_rotate(listener, log_file):
    """Vacía la cola de logging y fuerza la rotación => genera el .log.1.gz."""
    listener.stop()                 # espera a que se escriban todos los registros
    file_handler = listener.handlers[0]
    file_handler.doRollover()       # usa namer/rotator => .log.1.gz
    return log_file.parent / (log_file.name + ".1.gz")


def read_gz_lines(gz_path):
    with gzip.open(gz_path, "rt", encoding="utf-8") as fh:
        return fh.read().splitlines()


def test_log_gzip_exists_and_is_valid(forensic_env):
    """Verifica .log.gz."""
    logger, listener, log_file = forensic_env
    logger.info("evento de prueba para rotación")

    gz_path = flush_and_rotate(listener, log_file)

    assert gz_path.exists(), "No se generó el archivo .log.1.gz"
    assert gz_path.stat().st_size > 0
    # El archivo rotado sin comprimir debe haberse eliminado
    assert not (log_file.parent / (log_file.name + ".1")).exists()
    # Cabecera mágica de gzip
    assert gz_path.read_bytes()[:2] == b"\x1f\x8b"
    # Se descomprime completo sin errores y tiene contenido
    with gzip.open(gz_path, "rb") as fh:
        assert len(fh.read()) > 0


def test_forensic_fields_present(forensic_env):
    """Verifica campos forenses."""
    logger, listener, log_file = forensic_env
    logger.info(
        "Webhook verificado y encolado",
        extra={"trace_id": "trace-abc-123", "message_id": "msg-001"},
    )

    gz_path = flush_and_rotate(listener, log_file)
    record = json.loads(read_gz_lines(gz_path)[0])

    # Campos base
    assert REQUIRED_FIELDS <= record.keys()
    assert record["logger"] == "vulcano_engine"
    assert record["level"] == "INFO"
    assert record["message"] == "Webhook verificado y encolado"
    assert record["process"] == os.getpid()

    # Campos extra (TraceId, MessageId...) inyectados vía extra=
    assert record["trace_id"] == "trace-abc-123"
    assert record["message_id"] == "msg-001"

    # Timestamp ISO 8601 en UTC
    ts = datetime.fromisoformat(record["timestamp"])
    assert ts.utcoffset() == timedelta(0)


def test_json_lines_parseable_after_gzip(forensic_env):
    """Parseo línea por línea."""
    logger, listener, log_file = forensic_env
    messages = [f"evento {i}" for i in range(20)]
    messages.append("línea con ñ, tildes y \"comillas\"")
    messages.append("mensaje\ncon salto de línea")  # no debe romper el formato JSONL
    for msg in messages:
        logger.info(msg)

    gz_path = flush_and_rotate(listener, log_file)
    lines = read_gz_lines(gz_path)

    parsed = [json.loads(line) for line in lines]   # falla si alguna línea no es JSON
    assert len(parsed) == len(messages)
    assert [p["message"] for p in parsed] == messages
    assert all(isinstance(p, dict) for p in parsed)

def test_exception_notes_present_in_log(forensic_env):
    """Las notas de add_note() deben quedar en el log (contexto forense)."""
    logger, listener, log_file = forensic_env
    try:
        err = ValueError("fallo simulado")
        err.add_note("QueueUrl: http://localhost:4566/000000000000/vulcano-events-queue")
        raise err
    except ValueError:
        logger.exception("Error de prueba")

    gz_path = flush_and_rotate(listener, log_file)
    record = json.loads(read_gz_lines(gz_path)[0])

    assert "exception" in record
    assert record["exception"]["type"] == "ValueError"
    assert any("QueueUrl" in n for n in record["exception"]["notes"])
