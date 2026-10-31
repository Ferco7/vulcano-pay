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
    to_sign = f"{timestamp}.".encode("utf-8") + payload_bytes
    return hmac.new(secret.encode("utf-8"), to_sign, hashlib.sha256).hexdigest()


def verify_signature(secret: str, header_value: str, payload_bytes: bytes, tolerance_sec: int = 300) -> bool:
    """Verifica cabecera X-Webhook-Signature con timing-safe compare y ventana temporal."""
    # Verificación de existencia de la cabecera
    if not header_value:
        raise WebhookSignatureError("Cabecera X-Webhook-Signature ausente.")

    # Extracción de timestamp(t) y la firma (v1)
    parts = {}
    for item in header_value.split(","):
        #Verifica que el elemento de la cabecera tenga un = sino lo rechaza
        if "=" not in item:
            raise WebhookSignatureError(
                "Formato de cabecera inválido."
            )
        key, value = item.split("=", 1) 
        key = key.strip()
        value = value.strip()

        #Verifica que no haya campos duplicados
        if key in parts:
            raise WebhookSignatureError(
                "Campos duplicados en la cabecera."
            )
        
        parts[key] = value

    #Comprobacion de que existan la cadena de clave-valor en la cabecera X-Webhook-Signature obtenida 
    # en el bloque anterior
    if "t" not in parts or "v1" not in parts:
        raise WebhookSignatureError("Cabecera X-Webhook-Signature malformada.")

    # Validacion para timestamp
    try:
        timestamp = int(parts["t"])
    except ValueError:
        raise WebhookSignatureError("El timestamp de la cabecera no es un número entero válido.")
    # Validacion en caso de recibir un timestamp negativo
    if timestamp < 0:
        raise WebhookSignatureError("Timestamp inválido.")

    #Validar firma hexadecimal
    received_sig = parts["v1"]

    if len(received_sig) != 64:
        raise WebhookSignatureError("Longitud de firma incorrecta.")
    try:
        bytes.fromhex(received_sig)
    except ValueError:
        raise WebhookSignatureError("La firma no tiene formato hexadecimal válido.")
    
    #Prevencion de Replay Attacks
    current_time = int(time.time())
    if abs(current_time - timestamp) > tolerance_sec:
        raise WebhookTimestampError(f"Timestamp fuera de tolerancia ({abs(current_time - timestamp)}s > {tolerance_sec}s).")

    #Prevencion de Timing Attacks
    expected_sig = generate_signature(secret, timestamp, payload_bytes)
    if not hmac.compare_digest(expected_sig, received_sig):
        raise WebhookSignatureError("La firma HMAC-SHA256 no coincide.")

    return True
