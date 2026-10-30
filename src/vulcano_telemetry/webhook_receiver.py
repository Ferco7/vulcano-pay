from fastapi import FastAPI, Request, HTTPException, status
from .webhook_crypto import validar_firma_hmac, validar_timestamp
from .core_sqs import encolar_evento
from .exceptions import WebhookProcessingError

app = FastAPI()

WEBHOOK_SECRET = b"tu_secreto_compartido"

@app.post("/webhook", status_code=status.HTTP_202_ACCEPTED)
async def recibir_webhook(request: Request):
    try:
        # Validación obligatoria sobre los bytes crudos antes de llamar a .json()
        raw_body = await request.body()
        
        signature = request.headers.get("X-Hub-Signature-256", "")
        timestamp_header = request.headers.get("X-Timestamp", "0")
        
        try:
            timestamp = int(timestamp_header)
        except ValueError:
            raise HTTPException(status_code=400, detail="Timestamp inválido")
            
        if not validar_timestamp(timestamp):
            raise HTTPException(status_code=401, detail="Timestamp fuera de rango permitido")
            
        if not validar_firma_hmac(raw_body, signature, WEBHOOK_SECRET):
            raise HTTPException(status_code=401, detail="Firma HMAC inválida")
            
        encolar_evento(raw_body.decode("utf-8"))
        
        return {"status": "accepted", "message": "Evento encolado correctamente"}
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise WebhookProcessingError(f"Error interno procesando webhook: {str(e)}")

