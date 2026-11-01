Import re

def sanitizar_cadena(texto: str) -> str:
    """Limpia y sanitiza cadenas de texto de entrada."""
    if not isinstance(texto, str):
        return ""
    return re.sub(r'[^\w\s\-\.]', '', texto).strip()

