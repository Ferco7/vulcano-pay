import logging
import logging.handlers
import queue
from datetime import datetime, timezone

class ISO8601Formatter(logging.Formatter):
    """Formateador de logs en formato ISO 8601 UTC estricto."""
    def formatTime(self, record, datefmt=None):
        dt = datetime.fromtimestamp(record.created, tz=timezone.utc)
        return dt.isoformat()

def configurar_logging_asincrono():
    """Configura el sistema de logs con QueueHandler y QueueListener para desacoplar I/O."""
    log_queue = queue.Queue(-1)
    
    file_handler = logging.FileHandler("vulcano_events.log", encoding="utf-8")
    formatter = ISO8601Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    
    queue_handler = logging.handlers.QueueHandler(log_queue)
    
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(queue_handler)
    
    listener = logging.handlers.QueueListener(log_queue, file_handler, respect_handler_level=True)
    listener.start()
    return listener
