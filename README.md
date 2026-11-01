# TP-2: Sistema de Procesamiento de Eventos, Webhooks HMAC y Observabilidad Asíncrona con Boto3 y LocalStack (Proyecto Vulcano Pay)

## Integrantes

| Apellido y Nombre | Matrícula | Correo |
| ----------------- | --------- | ------ |
| Alegre Facundo Sebastian| ...       | ...    |
| ...               | ...       | ...    |
| ...               | ...       | ...    |
| ...               | ...       | ...    |
| ...               | ...       | ...    |
| ...               | ...       | ...    |


## Roles

| #   | Rol                                                                       | Archivo(s)                                                                         | Integrante |
| --- | ------------------------------------------------------------------------- | ---------------------------------------------------------------------------------- | ---------- |
| 1   | Ingeniero de Robustez de Entradas, Excepciones y Sanitización             | src/vulcano_telemetry/exceptions.py, src/vulcano_telemetry/sanitizer.py            | ...        |
| 2   | Ingeniero de Mensajería Asíncrona SQS con Boto3 y LocalStack              | src/vulcano_telemetry/core_sqs.py                                                  | ...        |
| 3   | Ingeniero de Seguridad Criptográfica HMAC y Servidor Receptor de Webhooks | src/vulcano_telemetry/webhook_crypto.py, src/vulcano_telemetry/webhook_receiver.py | ...        |
| 4   | Ingeniero de Almacenamiento, Observabilidad y Logging Estructurado JSON   | src/vulcano_telemetry/logging_engine.py                                            | Alegre Facundo Sebastian|
| 5   | Coordinador de Integración, Despachador Webhook y CLI Engine              | src/app_operator.py                                                                | ...        |
| 6   | Ingeniero de Simulación de Caos y Pruebas Forenses                        | tests/test_chaos.py, tests/test_forensic_log.py                                    | ...        |

## Instalación

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## Levantar LocalStack

```bash
docker compose up -d
```

## Tests

```bash
pytest -v
```
