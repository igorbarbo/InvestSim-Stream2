import pandas as pd

def calcular_investimento(inicial, mensal, taxa_anual, anos):
    """
    Calcula a evolução patrimonial com juros compostos mensais.
    """
    meses = anos * 12
    # Transforma taxa anual em mensal (juros compostos)
    taxa_mensal = (1 + taxa_anual/100)**(1/12) - 1
    
    saldo = inicial
    dados = []
    
    for mes in range(0, meses + 1):
        if mes > 0:
            juros = saldo * taxa_mensal
            saldo += juros + mensal
            
        dados.append({
            "Mês": mes, 
            "Saldo": round(saldo, 2),
            "Investido": round(inicial + (mensal * mes), 2)
        })
    
    return pd.DataFrame(dados)
    
