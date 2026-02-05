def annual_to_monthly(rate_annual: float) -> float:
    """Converte taxa anual para mensal (juros compostos)."""
    return (1 + rate_annual) ** (1/12) - 1

def adjust_for_inflation(value: float, inflation_annual: float, months: int) -> float:
    """Calcula o valor presente descontando a inflação acumulada."""
    monthly_inf = annual_to_monthly(inflation_annual)
    return value / ((1 + monthly_inf) ** months)
  
