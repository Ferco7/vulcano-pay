"""
Módulo de seguridad criptográfica HMAC-SHA256 para Webhooks.

responsable: integrante 3 - Seguridad Criptográfica HMAC y Servidor Receptor de Webhooks

OBJETIVO:
Generar y verificar firmas HMAC-SHA256 mitigando Replay y Timing Attacks.

REGLAS CRÍTICAS:
- Verificar SIEMPRE sobre bytes crudos del body (raw bytes).
- NUNCA verificar después de request.json().
- Header X-Webhook-Signature con formato t=timestamp,v1=signature
- Concatenación: f"{timestamp}.".encode("utf-8") + payload_bytes
- Usar hmac.compare_digest() obligatoriamente
- Ventana 300s -> WebhookTimestampError si |diff| > tolerance_sec
- Malformado/ausente o no coincide -> WebhookSignatureError
"""

import hmac
import hashlib
import time

from .exceptions import WebhookSignatureError, WebhookTimestampError


def generate_signature(secret: str, timestamp: int, payload_bytes: bytes) -> str:
    """Genera la firma HMAC-SHA256 en formato hexadecimal."""
    pass


def verify_signature(secret: str, header_value: str, payload_bytes: bytes, tolerance_sec: int = 300) -> bool:
    """Verifica cabecera X-Webhook-Signature con timing-safe compare y ventana temporal."""
    pass
