"""
Punto de entrada CLI ejecutable para VulcanoEventEngine.

responsable: integrante 5 - Integración, Despachador Webhook y CLI Engine

OBJETIVO:
Orquestar el flujo SQS <-> Webhooks con argparse, integración y captura quirúrgica.

MODOS:
- produce-sqs
- start-receiver
- start-dispatcher

REGLAS:
- Integrar todos los sanitizadores
- dispatch_webhook debe firmar y agregar header X-Webhook-Signature
- except* WebhookSignatureError, WebhookTimestampError, SQSConnectionError
- finally: apagar QueueListener. PROHIBIDO return/break/continue en finally (PEP 765)
"""

import argparse
import json
import logging
import os
import time
import requests
import uvicorn
from dotenv import load_dotenv

from vulcano_telemetry.sanitizer import (
    parse_queue_name,
    parse_wait_time,
    parse_webhook_url,
    parse_secret_key,
)
from vulcano_telemetry.core_sqs import get_sqs_client, consume_events, produce_event, delete_message
from vulcano_telemetry.webhook_crypto import generate_signature
from vulcano_telemetry.logging_engine import setup_vulcano_logging
from vulcano_telemetry.exceptions import (
    SQSConnectionError,
    WebhookSignatureError,
    WebhookTimestampError,
    WebhookDeliveryError,
    CorruptedMessageError,
)


logger = setup_vulcano_logging()


def build_parser() -> argparse.ArgumentParser:
    """Construye el parser de los argumentos con los subcomandos."""
    parser = argparse.ArgumentParser(
        prog="VulcanoCLI",
        description="Motor de Eventos SQS y Webhooks HMAC."
    )
    #subcomandos
    subparsers = parser.add_subparsers(dest="command", required=True, help="comandos disponibles")
    
    #comando 1: produce-sqs
    parser_produce = subparsers.add_parser("produce-sqs", help="publica un evento de prueba directamente a SQS LocalStack.")
    parser_produce.add_argument("-q", "--queue", type=parse_queue_name, default="vulcano-events-queue", help="Nombre de la cola SQS")
    parser_produce.add_argument("-m", "--message", default='{"transaction_id": "tx_9981","amount": 350.00, "status": "COMPLETED"}', help="Evento (JSON) a publicar")
    
    #comando 2: start-receiver
    parser_receiver = subparsers.add_parser("start-receiver", help="Inicia el servidor HTTP receptor de Webhooks.")
    parser_receiver.add_argument("--host", default="127.0.0.1", help="host del servidor (default: 127.0.01)")
    parser_receiver.add_argument("--port", type=int, default=8000, help="puerto del servidor (default:8000)")
    
    #comando 3: start-dispatcher
    parser_dispatcher = subparsers.add_parser("start-dispatcher", help="Ejecuta el  consumidor SQS  que despacha webhooks.")
    parser_dispatcher.add_argument("-q", "queue", type=parse_queue_name ,default="vulcano-events-queue", help="Nombre de la cola SQS")
    parser_dispatcher.add_argument("-w", "--wait-time",type=parse_wait_time, default=10, help="Tiempo de long polling (1-20s)")
    parser_dispatcher.add_argument("--url", type=parse_webhook_url, default="http://localhost:8000/webhook", help="url de destino del webhook")
    parser_dispatcher.add_argument("--secret", type=parse_secret_key,default=os.getenv("VULCANO_WEBHOOK_SECRET", "mi_clave_secreta_super_segura_vulcano_123"), help="clave  secreta HMAC")
    
    return parser


def dispatch_webhook(target_url: str, secret: str, payload_dict: dict):
    """Firma el payload y realiza HTTP POST iyectando la cabecera X-Webhook-Signature."""
    
    payload_bytes = json.dumps(payload_dict).encode("utf-8")
    timestamp = int(time.time())
    
    signature = generate_signature(secret, timestamp,payload_bytes)
    
    headers = {
        "Content-Type": "application/json",
        "X-Webhook-Signature": f"t={timestamp}, v1={signature}"
    }
    #Enviar peticion HTTP POST
    try:
        response = requests.post(target_url, data=payload_bytes, headers=headers, timeout=5)
        response.raise_for_status()
        logger.info(f"Webhook despachado existosamente a {target_url}. Status: {response.status_code}")
    
    except requests.exceptions.RequestException as err:
        delivery_err = WebhookDeliveryError(f"fallo al entregar Webhook a {target_url}")
        delivery_err.add_note(f"Detalle original: {str(err)}")
        raise delivery_err from err


def main():
    parser = build_parser
    args = parser.parse_args()
    
    logger.info(f"iniciando VulcanoCLI en modo '{args.command}'")
    
    try:
        #---COMANDO 1: PRODUCE-SQS ---
        if args.command == "produce-sqs":
            sqs = get_sqs_client()
            queue_url = f"http://localhost:4566/000000000000/{args.queue}"
            
            try:
                evento_prueba = json.loads(args.message)
                evento_prueba["timestamp"] =time.time()
            except json.JSONDecodeError:
                logger.error("el formato del mensaje no es un JSON valido. Usando evento por defecto.")
                evento_prueba = {"transaction_id": "tx_erro", "status": "FAILED"}
                
            msg_id = produce_event(sqs, queue_url, evento_prueba)
            logger.info(f"Evento de prueba publicado exitosamente. MessageID: {msg_id}")
            
        #---- COMANDO 2: START-RECEIVER ----
        elif args.command == "start-receiver":
            logger.info(f"Levantando servidor FastAPI en {args.host}:{args.port}...")
            #Inicia el servidor web de FastAPI
            uvicorn.run("vulcano_telemetry.webhook_receiver:app", host=args.host, port=args.port, log_config=None)
        
        #---- COMANDO 3: START-DISPATCHER ---
        elif args.command == "start-dispatcher":
            sqs = get_sqs_client()
            queue_url = f"http://localhost:4566/000000000000/{args.queue}" 
            logger.info("Iniciando Worker despachador (SQS -> Webhooks)...")
            
            #Bucle infinito de escucha
            while True:
                try:
                    events = consume_events(sqs, queue_url, wait_time=args.wait_time)
                    
                    for event in events:
                        try:
                            #  Despachar webhook
                            dispatch_webhook(args.url, args.secret, event["body"])
                            # si fue exitoso, borrar de SQS para que no se re-procese
                            delete_message(sqs,
                                           queue_url,
                                           event["receipt_handle"],
                                           )
                            
                        except WebhookDeliveryError as e:
                            # Si falla el envio, NO borramos el mensaje. SQS lo reintentara.
                            logger.error(f"Error despachando evento {event['message_id']}: {e}")
                            #si se superan los reintentos,  la Redrive Policy de la cola
                            #lo enviara automaticamente a la DLQ.
                
                except CorruptedMessageError as e:
                    #si el mensaje es venenoso (Poison Message), lo logueamos.
                    #No lo borramos; dejamos que SQS lo derive a la DLQ por reintentos.
                    logger.error(f"Mensaje corrupto detectado, derivando a DLQ: {e}")
    
                    
    except* WebhookSignatureError as group:
        logger.error(f"Errores de firma HMAC detectados ({len(group.exceptions)}):")
        for exc in group.exceptions:
            logger.error(f"  . {exc}")
    
    except* WebhookTimestampError as group:
            logger.error(f"Errores de Timestamp / Replay Attack detectados ({len(group.exceptions)}):")
            for exc in group.exceptions:
                logger.error(f"  . {exc}")
                
    except* SQSConnectionError as group:
            logger.error(f"Errores de comunicacion con SQS LocalStack ({len(group.exceptions)}):")
            for exc in group.exceptions:
                logger.error(f"  . {exc}")    
    
    except* WebhookDeliveryError as group:
             logger.error(f"Errores de entrega HTTP({len(group.exceptions)}):")
             for exc in group.exceptions:
                 logger.error(f"  . {exc}") 
                 
    
        
    finally:
        logger.info("Liberando recursos y cerrando pipeline de observabilidad")  
        listener = getattr(logger, "listener", None)
        if listener is not None:
            listener.stop()


if __name__ == "__main__":
    main()
