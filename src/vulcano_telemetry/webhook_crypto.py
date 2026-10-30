import hmac
import hashlib
import time

def validar_firma_hmac(body_bytes: bytes, signature_header: str, secret: bytes) -> bool:
    """Valida la firma HMAC-SHA256 utilizando obligatoriamente hmac.compare_digest."""
    if not signature_header:
        return False
    
    mac = hmac.new(secret, msg=body_bytes, digestmod=hashlib.sha256)
    expected_signature = f"sha256={mac.hexdigest()}"
    
    return hmac.compare_digest(expected_signature, signature_header)

def validar_timestamp(timestamp: int, max_delta_seconds: int = 300) -> bool:
    """Verifica que el timestamp esté dentro de la ventana permitida."""
    current_time = int(time.time())
    return abs(current_time - timestamp) <= max_delta_seconds
