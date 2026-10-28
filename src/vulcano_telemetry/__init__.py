"""
vulcano_telemetry
=================
Paquete de telemetría, mensajería SQS, Webhooks HMAC y logging forense
para el proyecto Vulcano Pay.

responsable: integracion (rol 5)
"""

from .exceptions import (
    VulcanoError,
    SQSConnectionError,
    QueueTimeoutError,
    CorruptedMessageError,
    WebhookSignatureError,
    WebhookTimestampError,
    WebhookDeliveryError,
)

from .sanitizer import (
    parse_queue_name,
    parse_wait_time,
    parse_webhook_url,
    parse_secret_key,
)

__all__ = [
    "VulcanoError",
    "SQSConnectionError",
    "QueueTimeoutError",
    "CorruptedMessageError",
    "WebhookSignatureError",
    "WebhookTimestampError",
    "WebhookDeliveryError",
    "parse_queue_name",
    "parse_wait_time",
    "parse_webhook_url",
    "parse_secret_key",
]
