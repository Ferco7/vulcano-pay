"""
Excepciones semánticas del ecosistema Vulcano Pay (SQS + Webhooks).

responsable: integrante 1 - Robustez de Entradas, Excepciones y Sanitización

NOTA:
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
    - Enriquecer con 'exc.add_note(...)' agregando QueueUrl / contexto
    """
    pass


class QueueTimeoutError(VulcanoError):
    """Lanzada ante timeouts relacionados con operaciones sobre colas SQS.
    
    NOTA:
    - Reservada para timeouts específicos del dominio de colas si aplica.
    """
    pass


class CorruptedMessageError(VulcanoError):
    """Lanzada cuando el cuerpo del mensaje SQS no es un JSON válido.
    
    MOMENTOS EN QUE SE USA:
    - Al hacer json.loads() sobre msg["Body"] en consume_events()
    
    NOTA:
    - Se considera un mensaje potencialmente corrupto/venenoso.
    - Debe tratarse según el flujo del dispatcher (reintentos / DLQ).
    """
    pass


class WebhookSignatureError(VulcanoError):
    """Lanzada cuando la firma criptográfica HMAC-SHA256 es inválida o ausente.
    
    MOMENTOS EN QUE SE USA:
    - Header X-Webhook-Signature malformado o ausente
    - Firma no coincide tras comparar con hmac.compare_digest()
    
    REGLAS:
    - SIEMPRE usar hmac.compare_digest() para mitigar Timing Attacks.
    """
    pass


class WebhookTimestampError(VulcanoError):
    """Lanzada cuando el timestamp del Webhook está fuera de la ventana de tolerancia.
    
    OBJETIVO:
    - Mitigar ataques de REPLAY (Replay Attacks)
    
    REGLAS:
    - Ventana por defecto: 300 segundos
    - Comparar |current_time - timestamp| > tolerance_sec
    """
    pass


class WebhookDeliveryError(VulcanoError):
    """Lanzada cuando el envío HTTP del Webhook falla tras reintentos.
    
    MOMENTOS EN QUE SE USA:
    - En dispatch_webhook() ante fallos de requests.post()
    - Ante errores de red / status inesperados según diseño del grupo
    """
    pass
