# Rentabilidades médias estimadas por classe de ativo
ASSET_RETURNS = {
    "Renda Fixa": 0.10,
    "Ações": 0.14,
    "Cripto": 0.25,
    "Global": 0.12
}

def portfolio_weighted_return(distribution: dict) -> float:
    """Calcula o retorno anual baseado na alocação (pesos de 0 a 1)."""
    total_return = 0.0
    for asset, weight in distribution.items():
        total_return += ASSET_RETURNS.get(asset, 0) * weight
    return total_return
  
