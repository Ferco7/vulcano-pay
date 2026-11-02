import boto3
from botocore.exceptions import BotoCoreError, ClientError

SQS_ENDPOINT = "http://localhost:4566"
QUEUE_NAME = "vulcano-events-queue"

def obtener_cliente_sqs():
    """Crea y retorna el cliente de SQS para LocalStack."""
    return boto3.client(
        "sqs",
        endpoint_url=SQS_ENDPOINT,
        region_name="us-east-1",
        aws_access_key_id="test",
        aws_secret_access_key="test"
    )

def get_sqs_client(endpoint_url: str = "http://localhost:4566"):
    """Crea una instancia del cliente Boto3 SQS configurada para LocalStack."""
    return obtener_cliente_sqs()

def encolar_evento(mensaje: str):
    """Envía un mensaje a la cola SQS de LocalStack."""
    sqs = obtener_cliente_sqs()
    try:
        response_url = sqs.get_queue_url(QueueName=QUEUE_NAME)
        queue_url = response_url["QueueUrl"]
        
        sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=mensaje
        )
    except (BotoCoreError, ClientError) as e:
        raise Exception(f"Error al conectar con SQS LocalStack: {e}")

def produce_event(sqs_client, queue_url: str, event_data: dict) -> str:
    """Publica un evento estructurado en la cola SQS usando Boto3."""
    import json
    try:
        payload = json.dumps(event_data)
        response = sqs_client.send_message(
            QueueUrl=queue_url,
            MessageBody=payload
        )
        msg_id = response.get("MessageId", "N/A")
        return msg_id
    except (BotoCoreError, ClientError) as err:
        from .exceptions import SQSConnectionError
        sqs_err = SQSConnectionError("Error al enviar mensaje a AWS SQS LocalStack.")
        sqs_err.add_note(f"QueueUrl: {queue_url}")
        raise sqs_err from err

def consume_events(sqs_client, queue_url: str, wait_time: int = 10, max_messages: int = 5):
    """Consume mensajes de SQS aplicando Long Polling y borrado explícito."""
    try:
        response = sqs_client.receive_message(
            QueueUrl=queue_url,
            MaxNumberOfMessages=max_messages,
            WaitTimeSeconds=wait_time,
            MessageAttributeNames=["All"]
        )
        messages = response.get("Messages", [])
        processed = []
        for msg in messages:
            processed.append({
                "receipt_handle": msg["ReceiptHandle"],
                "message_id": msg["MessageId"],
                "body": msg["Body"]
            })
        return processed
    except (BotoCoreError, ClientError) as err:
        from .exceptions import SQSConnectionError
        sqs_err = SQSConnectionError("Error en recepción de mensajes SQS.")
        raise sqs_err from err

def delete_message(sqs_client, queue_url: str, receipt_handle: str):
    """Elimina un mensaje procesado exitosamente de la cola SQS."""
    try:
        sqs_client.delete_message(
            QueueUrl=queue_url,
            ReceiptHandle=receipt_handle
        )
    except (BotoCoreError, ClientError) as err:
        from .exceptions import SQSConnectionError
        sqs_err = SQSConnectionError("Error al eliminar el mensaje procesado de SQS.")
        raise sqs_err from err
