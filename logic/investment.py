import numpy as np

def calcular_investimento(valor_inicial, aporte_mensal, taxa_anual, meses):
    """
    Realiza o cálculo de juros compostos. 
    Garante que o retorno seja um número real (float) para evitar o erro st.metric.
    """
    try:
        # Converte taxa anual para mensal
        taxa_mensal = (1 + float(taxa_anual))**(1/12) - 1
        meses = int(meses)
        
        # Fórmula de juros compostos para o montante inicial
        total = valor_inicial * (1 + taxa_mensal)**meses
        
        # Soma os aportes mensais com juros
        if aporte_mensal > 0:
            for i in range(1, meses + 1):
                total += aporte_mensal * (1 + taxa_mensal)**(meses - i)
        
        return float(total)
    except Exception:
        return 0.0
        
