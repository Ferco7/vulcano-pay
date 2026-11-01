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


