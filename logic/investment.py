# logic/investment.py

def simulate_investment(amount: float, rate: float, years: int) -> float:
    """
    Simula o valor futuro de um investimento simples composto.
    amount : Valor inicial investido
    rate   : Taxa de retorno anual (em decimal, ex: 0.05 = 5%)
    years  : Número de anos
    """
    return amount * (1 + rate) ** years
