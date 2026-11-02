"""
Tests para VulcanoEventEngine.

responsable: integrante 6 - Simulación de Caos y Pruebas Forenses

OBJETIVO:
Validar la inyección de caos en el sistema de procesamiento de eventos,
firmas inválidas y mensajes venenosos hacia la Dead Letter Queue (DLQ).
"""

import json
import time
import uuid

import pytest

from vulcano_telemetry.exceptions import WebhookSignatureError, WebhookTimestampError
from vulcano_telemetry.webhook_crypto import generate_signature, verify_signature

SECRET = "clave_de_prueba_vulcano_123"
PAYLOAD = json.dumps(
    {"transaction_id": "tx_9981", "amount": 350.0, "status": "COMPLETED"}
).encode("utf-8")


def build_header(secret: str, payload: bytes, timestamp: int | None = None) -> str:
    """Arma la cabecera X-Webhook-Signature igual que dispatch_webhook."""
    ts = int(time.time()) if timestamp is None else timestamp
    sig = generate_signature(secret, ts, payload)
    return f"t={ts}, v1={sig}"


# --------------------------------------------------------------------------
# Línea base: sin esto, los tests de caos no demuestran nada
# --------------------------------------------------------------------------
def test_valid_signature_is_accepted_baseline():
    """Firma correcta + timestamp actual => True (control del experimento)."""
    header = build_header(SECRET, PAYLOAD)
    assert verify_signature(SECRET, header, PAYLOAD) is True


# --------------------------------------------------------------------------
# 1) Firmas inválidas
# --------------------------------------------------------------------------
def test_invalid_signature_rejected():
    """Firmas alteradas/clave incorrecta."""
    # a) Clave incorrecta
    header = build_header("otra_clave_totalmente_distinta", PAYLOAD)
    with pytest.raises(WebhookSignatureError, match="no coincide"):
        verify_signature(SECRET, header, PAYLOAD)

    # b) Payload alterado en tránsito (la firma era de otro cuerpo)
    header = build_header(SECRET, PAYLOAD)
    tampered = PAYLOAD.replace(b"350.0", b"999999.0")
    with pytest.raises(WebhookSignatureError, match="no coincide"):
        verify_signature(SECRET, header, tampered)

    # c) Firma alterada (mismo largo, un carácter distinto)
    ts = int(time.time())
    good_sig = generate_signature(SECRET, ts, PAYLOAD)
    bad_sig = ("0" if good_sig[0] != "0" else "1") + good_sig[1:]
    with pytest.raises(WebhookSignatureError, match="no coincide"):
        verify_signature(SECRET, f"t={ts}, v1={bad_sig}", PAYLOAD)


@pytest.mark.parametrize(
    "header",
    [
        None,                          # cabecera ausente
        "",                            # cabecera vacía
        "basura_sin_igual",            # sin '='
        "t=123",                       # falta v1
        f"v1={'a' * 64}",              # falta t
        f"t=abc, v1={'a' * 64}",       # timestamp no numérico
        f"t=-5, v1={'a' * 64}",        # timestamp negativo
        f"t=1, t=2, v1={'a' * 64}",    # campos duplicados
        "t=123, v1=abc",               # firma de largo incorrecto
        f"t=123, v1={'z' * 64}",       # largo OK pero no hexadecimal
    ],
    ids=[
        "ausente", "vacia", "sin_igual", "falta_v1", "falta_t",
        "t_no_numerico", "t_negativo", "duplicados", "firma_corta", "no_hex",
    ],
)
def test_malformed_signature_header_rejected(header):
    """Cabeceras malformadas siempre terminan en WebhookSignatureError."""
    with pytest.raises(WebhookSignatureError):
        verify_signature(SECRET, header, PAYLOAD)


# --------------------------------------------------------------------------
# 2) Replay attacks
# --------------------------------------------------------------------------
def test_replay_attack_rejected_by_timestamp():
    """Timestamp fuera de ventana."""
    # Firma 100% válida, pero capturada hace 10 minutos => replay
    old_ts = int(time.time()) - 600
    header = build_header(SECRET, PAYLOAD, timestamp=old_ts)
    with pytest.raises(WebhookTimestampError, match="fuera de tolerancia"):
        verify_signature(SECRET, header, PAYLOAD)

    # Timestamp del futuro también se rechaza (ventana simétrica)
    future_ts = int(time.time()) + 600
    header = build_header(SECRET, PAYLOAD, timestamp=future_ts)
    with pytest.raises(WebhookTimestampError):
        verify_signature(SECRET, header, PAYLOAD)

    # Tolerancia configurable: 10 s de antigüedad con ventana de 5 s
    header = build_header(SECRET, PAYLOAD, timestamp=int(time.time()) - 10)
    with pytest.raises(WebhookTimestampError):
        verify_signature(SECRET, header, PAYLOAD, tolerance_sec=5)


def test_replay_inside_window_is_accepted():
    """Borde: dentro de la ventana de 300 s sigue siendo válido."""
    header = build_header(SECRET, PAYLOAD, timestamp=int(time.time()) - 290)
    assert verify_signature(SECRET, header, PAYLOAD) is True


def test_replay_with_refreshed_timestamp_fails_signature():
    """El atacante renueva 't' pero conserva la firma vieja: la firma no coincide."""
    old_ts = int(time.time()) - 600
    old_sig = generate_signature(SECRET, old_ts, PAYLOAD)
    forged_header = f"t={int(time.time())}, v1={old_sig}"
    with pytest.raises(WebhookSignatureError, match="no coincide"):
        verify_signature(SECRET, forged_header, PAYLOAD)


# --------------------------------------------------------------------------
# 3) Nivel HTTP: el receptor FastAPI responde 401 y NO encola
# --------------------------------------------------------------------------
@pytest.fixture
def receiver_client(monkeypatch):
    pytest.importorskip("httpx")  # requerido por TestClient
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient
    from vulcano_telemetry import webhook_receiver

    enqueued = []
    monkeypatch.setattr(webhook_receiver, "WEBHOOK_SECRET", SECRET)
    monkeypatch.setattr(
        webhook_receiver,
        "produce_event",
        lambda client, url, data: enqueued.append(data) or "msg-fake-1",
    )
    return TestClient(webhook_receiver.app), enqueued


def test_receiver_rejects_bad_signature_with_401(receiver_client):
    client, enqueued = receiver_client
    headers = {
        "Content-Type": "application/json",
        "X-Webhook-Signature": build_header("clave_incorrecta_123456", PAYLOAD),
    }
    resp = client.post("/webhook", content=PAYLOAD, headers=headers)
    assert resp.status_code == 401
    assert enqueued == []  # nada llegó a SQS


def test_receiver_rejects_replay_with_401(receiver_client):
    client, enqueued = receiver_client
    headers = {
        "Content-Type": "application/json",
        "X-Webhook-Signature": build_header(
            SECRET, PAYLOAD, timestamp=int(time.time()) - 600
        ),
    }
    resp = client.post("/webhook", content=PAYLOAD, headers=headers)
    assert resp.status_code == 401
    assert enqueued == []


def test_receiver_accepts_valid_webhook_with_202(receiver_client):
    client, enqueued = receiver_client
    headers = {
        "Content-Type": "application/json",
        "X-Webhook-Signature": build_header(SECRET, PAYLOAD),
    }
    resp = client.post("/webhook", content=PAYLOAD, headers=headers)
    assert resp.status_code == 202
    assert enqueued == [json.loads(PAYLOAD)]


# --------------------------------------------------------------------------
# 4) Mensajes venenosos -> DLQ (integración con LocalStack)
# --------------------------------------------------------------------------
@pytest.fixture
def sqs_with_dlq():
    """Crea cola + DLQ temporales en LocalStack. Se saltea si no está levantado."""
    pytest.importorskip("boto3")
    from vulcano_telemetry.core_sqs import get_sqs_client

    sqs = get_sqs_client()
    try:
        sqs.list_queues()
    except Exception:
        pytest.skip("LocalStack no disponible en localhost:4566 (docker compose up -d)")

    suffix = uuid.uuid4().hex[:8]
    dlq_url = sqs.create_queue(QueueName=f"vulcano-test-{suffix}-dlq")["QueueUrl"]
    dlq_arn = sqs.get_queue_attributes(
        QueueUrl=dlq_url, AttributeNames=["QueueArn"]
    )["Attributes"]["QueueArn"]
    queue_url = sqs.create_queue(
        QueueName=f"vulcano-test-{suffix}-queue",
        Attributes={
            "VisibilityTimeout": "1",
            "RedrivePolicy": json.dumps(
                {"deadLetterTargetArn": dlq_arn, "maxReceiveCount": "1"}
            ),
        },
    )["QueueUrl"]

    yield sqs, queue_url, dlq_url

    for url in (queue_url, dlq_url):
        sqs.delete_queue(QueueUrl=url)


def test_poison_message_goes_to_dlq(sqs_with_dlq):
    """Mensajes venenosos hacia DLQ."""
    from vulcano_telemetry.core_sqs import consume_events

    sqs, queue_url, dlq_url = sqs_with_dlq
    poison_body = "{esto no es un json valido"

    # produce_event() hace json.dumps, así que el veneno se envía directo con boto3
    sqs.send_message(QueueUrl=queue_url, MessageBody=poison_body)

    # 1) El consumidor lo recibe y comprueba que es venenoso (no parsea)
    first = consume_events(sqs, queue_url, wait_time=2)
    assert len(first) == 1
    assert first[0]["body"] == poison_body
    with pytest.raises(json.JSONDecodeError):
        json.loads(first[0]["body"])
    # ...y NO se borra (igual que hace el dispatcher), así SQS reintenta.

    # 2) Superado maxReceiveCount, la Redrive Policy lo mueve a la DLQ
    time.sleep(2)  # > VisibilityTimeout
    found = []
    deadline = time.time() + 20
    while not found and time.time() < deadline:
        consume_events(sqs, queue_url, wait_time=1)       # dispara el redrive
        found = consume_events(sqs, dlq_url, wait_time=1)

    assert len(found) == 1, "El mensaje venenoso no llegó a la DLQ"
    assert found[0]["body"] == poison_body
