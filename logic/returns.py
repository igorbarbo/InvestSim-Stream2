def real_return(nominal: float, inflation: float) -> float:
    """Calcula a rentabilidade real usando a Equação de Fisher."""
    # i_real = [(1 + i_nom) / (1 + i_inf)] - 1
    return ((1 + nominal) / (1 + inflation)) - 1
  
