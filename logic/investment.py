def calcular_patrimonio(v_inicial, aporte, taxa_mensal_perc, meses):
    """
    Calcula o crescimento de patrimônio. 
    Serve para Ações (taxa = valorização) e FIIs (taxa = dividendos).
    """
    try:
        total = float(v_inicial)
        taxa = float(taxa_mensal_perc) / 100
        for _ in range(int(meses)):
            # Aplica a taxa sobre o montante e soma o aporte
            total = (total * (1 + taxa)) + float(aporte)
        return float(total)
    except:
        return 0.0
        
