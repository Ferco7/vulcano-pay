"""
Configuración compartida de pytest para VulcanoEventEngine.

Agrega la carpeta src/ al sys.path para poder hacer:
    from vulcano_telemetry... import ...
sin instalar el paquete.
"""

import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
