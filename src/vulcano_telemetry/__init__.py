"""
vulcano_telemetry
=================
Paquete de telemetría, mensajería SQS, Webhooks HMAC y logging forense
para el proyecto Vulcano Pay.

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

from .core_sqs import (
    get_sqs_client,
    produce_event,
    consume_events,
    delete_message,
)

from .webhook_crypto import (
    generate_signature,
    verify_signature,
)

from .logging_engine import (
    setup_vulcano_logging,
    AsyncJSONFormatter,
    
)

__all__ = [
    #Excepciones
    "VulcanoError",
    "SQSConnectionError",
    "QueueTimeoutError",
    "CorruptedMessageError",
    "WebhookSignatureError",
    "WebhookTimestampError",
    "WebhookDeliveryError",
    
    #Sanitizacion
    "parse_queue_name",
    "parse_wait_time",
    "parse_webhook_url",
    "parse_secret_key",
    
    #sqs
    "get_sqs_client",
    "produce_event",
    "consume_events",
    "delete_message",
    
    #crypto
    "generate_signature",
    "verify_signature",
    
    #Logging
    "setup_vulcano_logging"
    "AsyncJSONFormatter",
    
]
