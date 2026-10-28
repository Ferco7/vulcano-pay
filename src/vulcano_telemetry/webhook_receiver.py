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

import logging

from fastapi import FastAPI, Request, HTTPException, status

from .webhook_crypto import verify_signature
from .core_sqs import get_sqs_client, produce_event
from .exceptions import WebhookSignatureError, WebhookTimestampError

logger = logging.getLogger("vulcano_engine")
app = FastAPI(title="Vulcano Webhook Receiver", version="1.0.0")

WEBHOOK_SECRET = "mi_clave_secreta_super_segura_vulcano_123"
QUEUE_URL = "http://localhost:4566/000000000000/vulcano-events-queue"
sqs_client = get_sqs_client()


@app.post("/webhook", status_code=status.HTTP_202_ACCEPTED)
async def receive_webhook(request: Request):
    """Valida firma sobre raw bytes, responde 202 y encola en SQS."""
    pass
