def real_return(future_value, inflation_rate, years):
    """
    Ajusta o valor futuro pela inflação.
    """
    return round(future_value / ((1 + inflation_rate) ** years), 2)
