# utils/validators.py
import re

def validar_ticker(ticker: str) -> bool:
    """Valida formato básico de ticker (B3 ou internacional)."""
    ticker = ticker.upper().strip()
    return bool(re.match(r'^[A-Z]{4}(3|4|11)$|^[A-Z]{1,5}$', ticker))

def validar_percentual(valor: float) -> bool:
    """Valida percentual entre 0 e 100."""
    return 0 <= valor <= 100

def normalizar_ticker(ticker: str) -> str:
    """Normaliza ticker para upper e sem espaços."""
    return ticker.upper().strip()
