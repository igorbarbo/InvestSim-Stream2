import pandas as pd

def calcular_investimento(inicial, mensal, taxa_anual, anos):
    """Calcula a evolução patrimonial detalhada."""
    meses = anos * 12
    taxa_mensal = (1 + taxa_anual/100)**(1/12) - 1
    
    saldo = inicial
    dados = []
    
    for mes in range(0, meses + 1):
        if mes > 0:
            juros = saldo * taxa_mensal
            saldo += juros + mensal
            
        dados.append({
            "Mês": mes, 
            "Patrimônio Total": round(saldo, 2),
            "Total Investido": round(inicial + (mensal * mes), 2)
        })
    
    return pd.DataFrame(dados)

def obter_taxa_cenario(perfil):
    """Retorna taxas médias baseadas no perfil de risco."""
    cenarios = {
        "Conservador": 10.5,
        "Moderado": 13.0,
        "Agressivo": 16.5
    }
    return cenarios.get(perfil, 10.0)
    
