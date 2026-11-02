import re
import argparse
from urllib.parse import urlparse

def sanitizar_cadena(texto: str) -> str:
    """Limpia y sanitiza cadenas de texto de entrada."""
    if not isinstance(texto, str):
        return ""
    return re.sub(r'[^\w\s\-\.]', '', texto).strip()

def parse_queue_name(value: str) -> str:
    """Valida que el nombre de la cola SQS cumpla con el patrón vulcano-[a-z0-9-]+-queue.
    
    NOTAS:
    - Definir patrón r"^vulcano-[a-z0-9-]+-queue$"
    - Validar con re.match
    - Si no coincide lanzar argparse.ArgumentTypeError
    - Retornar value si coincide
    """
    pattern = r"^vulcano-[a-z0-9-]+-queue$"
    if not re.match(pattern, value):
        raise argparse.ArgumentTypeError(
            f"Nombre de cola inválido '{value}'. Debe seguir el patrón 'vulcano-<nombre>-queue'."
        )
    return value

def parse_wait_time(value: str) -> int:
    """Sanitiza el tiempo de Long Polling para SQS (WaitTimeSeconds entre 1 y 20 segundos).
    
    NOTAS:
    - Convertir a int
    - Validar rango 1 <= val <= 20
    - Lanzar argparse.ArgumentTypeError si no es válido
    """
    try:
        val = int(value)
        if not (1 <= val <= 20):
            raise ValueError()
        return val
    except ValueError:
        raise argparse.ArgumentTypeError(f"WaitTimeSeconds inválido '{value}'. Debe ser entre 1 y 20 s.")

def parse_webhook_url(value: str) -> str:
    """Valida que la URL del receptor sea un HTTP/HTTPS válido (ej.: http://localhost:8000/webhook)."""
    parsed = urlparse(value)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise argparse.ArgumentTypeError(f"URL de Webhook inválida '{value}'. Debe ser HTTP/HTTPS.")
    return value

def parse_secret_key(value: str) -> str:
    """Valida que la clave secreta HMAC tenga al menos 16 caracteres."""
    if len(value) < 16:
        raise argparse.ArgumentTypeError("La clave secreta HMAC debe tener al menos 16 caracteres.")
    return value
