"""Engine de observabilidad con formato JSON, QueueHandler y compresión Gzip."""

import gzip
import json
import logging
import logging.handlers
import os
import queue
import shutil
import copy
from datetime import datetime, timezone
from typing import Any, Dict

class AsyncJSONFormatter(logging.Formatter):
    """Formateador JSON estructurado conforme a ISO 8601 UTC."""

    def format(self, record: logging.LogRecord) -> str:
        # 1. Estructura base del LogRecord
        log_data: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "logger": record.name,
            "level": record.levelname,
            "message": record.getMessage(),
            "process": record.process,
            "threadName": record.threadName,
        }

        # 2. Inyección de atributos extra (TraceId, MessageId, WebhookId, etc.)
        # Buscamos en el __dict__ del record para capturar todo lo que se pasó por 'extra='
        standard_attrs = {
            'name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 'filename',
            'module', 'exc_info', 'exc_text', 'stack_info', 'lineno', 'funcName',
            'created', 'msecs', 'relativeCreated', 'thread', 'threadName',
            'processName', 'process', 'message', 'taskName'
        }
        for key, value in record.__dict__.items():
            if key not in standard_attrs:
                log_data[key] = value

        # 3. Serialización recursiva de excepciones (ExceptionGroup)
        if record.exc_info:
            log_data["exception"] = self._format_exception_tree(record.exc_info[1])

        return json.dumps(log_data, ensure_ascii=False, default=str)

    def _format_exception_tree(self, exc: Exception) -> Dict[str, Any]:
        """Extrae recursivamente el árbol de excepciones y sus notas."""
        exc_data = {
            "type": type(exc).__name__,
            "message": str(exc),
            "notes": getattr(exc, "__notes__", []),
        }

        # Si es un ExceptionGroup (PEP 654), procesar sus excepciones anidadas
        if hasattr(exc, "exceptions"):
            exc_data["sub_exceptions"] = [
                self._format_exception_tree(sub_exc) for sub_exc in exc.exceptions
            ]
        
        return exc_data

def gzip_namer(default_name: str) -> str:
    """Callback para renombrar el archivo rotado agregando la extensión .gz."""
    return default_name + ".gz"

def gzip_rotator(source: str, dest: str) -> None:
    """Callback para comprimir el archivo rotado usando gzip."""
    with open(source, "rb") as f_in:
        with gzip.open(dest, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)
    os.remove(source)

class VulcanoQueueHandler(logging.handlers.QueueHandler):
    """QueueHandler que preserva el LogRecord original (msg + exc_info) al pasar por la cola.

    El QueueHandler base de la stdlib en su metodo 'prepare()' reemplaza 'msg' por el
    mensaje ya formateado y zankea ('msg', 'args', 'exc_info', 'exc_text', 'stack_info')
    los atributos del record antes de encolarlo. Con el AsyncJSONFormatter del listener
    eso descarta el exc_info y contamina el 'message' con el traceback de texto plano.

    Esta subclase encola una copia del record sin modificar nada, para que el formatter
    del listener pueda construir el JSON estructurado con el campo 'exception'.
    """

    def prepare(self, record: logging.LogRecord) -> logging.LogRecord:
        return copy.copy(record)

def setup_vulcano_logging(log_filename: str = "vulcano_events.log") -> logging.Logger:
    """Configura el pipeline de logging no bloqueante mediante QueueHandler y QueueListener."""
    
    # 1. Cola segura en memoria
    log_queue = queue.Queue(-1)
    queue_handler = VulcanoQueueHandler(log_queue)

    # 2. Handler de archivo con rotación y compresión
    file_handler = logging.handlers.RotatingFileHandler(
        filename=log_filename,
        maxBytes=2 * 1024 * 1024,  # 2 MB
        backupCount=3,             # Máximo 3 respaldos
        encoding="utf-8"
    )
    file_handler.setFormatter(AsyncJSONFormatter())
    file_handler.namer = gzip_namer
    file_handler.rotator = gzip_rotator

    # 3. Listener en hilo secundario
    listener = logging.handlers.QueueListener(log_queue, file_handler)
    listener.start()

    # 4. Configurar Logger
    logger = logging.getLogger("vulcano_engine")
    logger.setLevel(logging.INFO)
    logger.addHandler(queue_handler)
    
    # Guardamos el listener en el logger para poder detenerlo en el finally de app_operator.py
    logger.listener = listener
    
    return logger