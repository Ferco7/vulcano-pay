"""
Excepciones semánticas del ecosistema Vulcano Pay (SQS + Webhooks).

responsable: integrante 1 - Robustez de Entradas, Excepciones y Sanitización

OBJETIVO:
Excepción base del ecosistema con todas las excepciones de dominio SQS y Webhooks.

REGLAS:
- Todas las excepciones personalizadas DEBEN heredar de Exception.
- PROHIBIDO heredar de BaseException.
- Se debe hacer uso de add_note() para agregar contexto forense cuando corresponda.
"""


class VulcanoError(Exception):
    """Excepción base para todos los errores del ecosistema Vulcano Pay.
    
    Nunca heredar de BaseException. Todas las subclases deben heredar
    directamente o indirectamente de VulcanoError.
    """
    pass


class SQSConnectionError(VulcanoError):
    """Lanzada ante fallos de comunicación con AWS SQS / LocalStack.
    
    MOMENTOS EN QUE SE USA:
    - Al crear / utilizar el cliente boto3 hacia LocalStack
    - Al enviar mensajes con send_message()
    - Al recibir mensajes con receive_message()
    
    RECOMENDACIÓN:
    - Encadenar con 'raise ... from err' (raise from ClientError)
    - Enriquecer con 'exc.add_note(...)' 
    """
    pass


class QueueTimeoutError(VulcanoError):
    """Lanzada ante timeouts en la cola SQS / long polling."""
    pass


class CorruptedMessageError(VulcanoError):
    """Lanzada cuando el cuerpo del mensaje SQS no es un JSON válido."""
    pass


class WebhookSignatureError(VulcanoError):
    """Lanzada cuando la firma HMAC-SHA256 es inválida o ausente."""
    pass


class WebhookTimestampError(VulcanoError):
    """Lanzada cuando el timestamp del Webhook está fuera de la ventana de tolerancia (Replay Attack)."""
    pass


class WebhookDeliveryError(VulcanoError):
    """Lanzada cuando el fallo HTTP del Webhook al emisor ocurre tras reintentos."""
    pass


class WebhookProcessingError(VulcanoError):
    """Excepción lanzada cuando falla el procesamiento del webhook."""
    pass


class InvalidSignatureError(VulcanoError):
    """Excepción lanzada cuando la firma HMAC es inválida."""
    pass


class InvalidTimestampError(VulcanoError):
    """Excepción lanzada cuando la timestamp excede la ventana permitida."""
    pass
