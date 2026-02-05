# Calcula o retorno real descontando a inflação
def real_return(amount: float, rate: float, inflation: float) -> float:
    """
    amount    : Valor futuro nominal
    rate      : Taxa de retorno anual nominal (em decimal)
    inflation : Inflação anual (em decimal)
    """
    # Fórmula simples para valor real
    return amount / (1 + inflation)
