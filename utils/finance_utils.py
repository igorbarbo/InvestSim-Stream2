import numpy as np
import pandas as pd

def retorno_mensal(series: pd.Series) -> pd.Series:
    """Calcula o retorno percentual mensal de uma série de preços"""
    return series.pct_change().dropna()

def volatilidade_anual(series: pd.Series) -> float:
    """Calcula a volatilidade anualizada de uma série de preços"""
    return retorno_mensal(series).std() * (12 ** 0.5)

def max_drawdown(series: pd.Series) -> float:
    """Calcula o Max Drawdown de uma série de preços"""
    pico = series.cummax()
    return ((series - pico) / pico).min()

def sharpe(series: pd.Series, rf: float = 0.0) -> float:
    """Calcula o Sharpe Ratio anualizado de uma série de preços"""
    r = retorno_mensal(series)
    if r.std() == 0:
        return 0
    return (r.mean() - rf / 12) / r.std() * (12 ** 0.5)
