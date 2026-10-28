"""
Validadores sanitizadores declarativos para la CLI de VulcanoEventEngine.

responsable: integrante 1 - Robustez de Entradas, Excepciones y Sanitización

OBJETIVO:
Implementar validadores custom para argparse que saniticen los argumentos
del CLI ANTES de iniciar cualquier conexión con LocalStack / SQS / Webhooks.

REGLAS OBLIGATORIAS:
- Los validadores deben lanzar argparse.ArgumentTypeError con mensajes claros y descriptivos.
- Utilizar expresiones regulares (re) y urllib.parse según corresponda.
- Mantener lógica PURA (sin side effects).
- NO modificar imports ni firmas.
"""

import argparse
import re
from urllib.parse import urlparse


def parse_queue_name(value: str) -> str:
    """Valida que el nombre de la cola SQS cumpla con el patrón vulcano-[a-z0-9-]+-queue.
    
    NOTAS:
    - Definir patrón r"^vulcano-[a-z0-9-]+-queue$"
    - Validar con re.match
    - Si no coincide lanzar argparse.ArgumentTypeError
    - Retornar value si coincide
    """
    pass


def parse_wait_time(value: str) -> int:
    """Sanitiza el tiempo de Long Polling para SQS (WaitTimeSeconds entre 1 y 20 segundos).
    
    NOTAS:
    - Convertir a int
    - Validar rango 1 <= val <= 20
    - Lanzar argparse.ArgumentTypeError si no es entero o fuera de rango
    - Retornar valor entero
    """
    pass


def parse_webhook_url(value: str) -> str:
    """Valida que la URL del webhook tenga esquema HTTP o HTTPS válido.
    
    NOTAS:
    - Parsear con urllib.parse.urlparse
    - scheme debe ser 'http' o 'https'
    - netloc debe existir
    - Lanzar argparse.ArgumentTypeError si falla
    - Retornar URL validada
    """
    pass


def parse_secret_key(value: str) -> str:
    """Valida que la clave secreta HMAC tenga al menos 16 caracteres.
    
    NOTAS:
    - Verificar len(value) >= 16
    - Lanzar argparse.ArgumentTypeError si es menor
    - Retornar clave validada
    """
    pass
