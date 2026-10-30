class VulcanoError(Exception):
    """Excepción base para errores del motor Vulcano."""
    pass

class WebhookProcessingError(VulcanoError):
    """Excepción lanzada cuando falla el procesamiento del webhook."""
    pass

class InvalidSignatureError(VulcanoError):
    """Excepción lanzada cuando la firma HMAC es inválida."""
    pass

class InvalidTimestampError(VulcanoError):
    """Excepción lanzada cuando el timestamp excede la ventana permitida."""
    pass



  
  
