"""
Servidor HTTP Receptor de Webhooks utilizando FastAPI y Boto3 hacia LocalStack.

responsable: integrante 3 - Seguridad Criptográfica HMAC y Servidor Receptor de Webhooks

OBJETIVO:
Validar firma sobre raw bytes, responder 202 Accepted y encolar en SQS.

FLUJO OBLIGATORIO:
1) raw_bytes = await request.body() ANTES de request.json()
2) Obtener X-Webhook-Signature
3) verify_signature con raw_bytes
4) Si error -> logger.warning + HTTPException(401)
5) Si ok -> payload = await request.json() + produce_event + responder 202
"""

import os
from dotenv import load_dotenv

import logging
import asyncio
from fastapi import FastAPI, Request, HTTPException, status

from .webhook_crypto import verify_signature
from .core_sqs import get_sqs_client, produce_event
from .exceptions import WebhookSignatureError, WebhookTimestampError

load_dotenv()

logger = logging.getLogger("vulcano_engine")
app = FastAPI(title="Vulcano Webhook Receiver", version="1.0.0")

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")
QUEUE_URL = os.getenv("SQS_QUEUE_UR")
sqs_client = get_sqs_client()

if not WEBHOOK_SECRET:
    raise RuntimeError("Falta configurar VULCANO_WEBHOOK_SECRET")

if not QUEUE_URL:
    raise RuntimeError("Falta configurar SQS_QUEUE_URL")

@app.post("/webhook", status_code=status.HTTP_202_ACCEPTED)
async def receive_webhook(request: Request):
    """Valida firma sobre raw bytes, responde 202 y encola en SQS."""

    #Se obtienen los bytes crudos de la peticion para verificar la firma
    raw_bytes = await request.body()
    
    #Se extrae el X-Webhook-Signature del header de la peticion
    signature_header = request.headers.get("X-Webhook-Signature")

    try:
        #De la firma obtenida se calcula que las firmas del emisor como del receptor coincidan 
        verify_signature(WEBHOOK_SECRET, signature_header, raw_bytes)
        
    except (WebhookSignatureError, WebhookTimestampError) as err:
        # Si la firma es incorrecta o el timestamp esta fuera del rango permitido
        # se registra en el log y se lanza una HTTPException
        logger.warning(f"Rechazado Webhook no autenticado: {err}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(err))

    # Si la firma es valida, se convierte el contenido del JSON a un objeto python
    payload = await request.json()
    
    # Usamos asyncio.to_thread para que produce_event (Boto3) no bloquee el servidor
    msg_id = await asyncio.to_thread(produce_event, sqs_client, QUEUE_URL, payload)
    
    logger.info(f"Webhook verificado y encolado exitosamente en SQS. MessageId: {msg_id}")
    
    # Devuelve HTTP 202 Accepted (ya definido como decorador arriba de la firma)
    return {"status": "accepted", "message_id": msg_id}
