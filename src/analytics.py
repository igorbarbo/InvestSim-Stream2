import pandas as pd

def process_metrics(df):
    """
    Motor Financeiro de Precisão: Calcula métricas ponderadas pelo patrimônio.
    """
    # 1. Cálculos Básicos
    df['Preço Atual'] = pd.to_numeric(df['Preço Atual'], errors='coerce')
    df['Patrimônio'] = df['QTD'] * df['Preço Atual']
    
    # 2. Rentabilidade Individual Ponderada
    # (Preço Atual / Preço Médio - 1) * 100
    df['Valorização %'] = (df['Preço Atual'] / df['Preço Médio'] - 1) * 100
    
    # 3. Métricas Consolidadas (O Pulo do Gato para nota 9,5)
    total_patrimonio = df['Patrimônio'].sum()
    
    # Rentabilidade Real da Carteira (Ponderada pelo peso de cada ativo)
    # Fórmula: Soma(Valorizacao_Ativo * Peso_do_Ativo)
    rentabilidade_ponderada = (df['Valorização %'] * df['Patrimônio']).sum() / total_patrimonio
    
    # 4. Cálculo de Prioridade (Motor Decisional Simples)
    # Dá mais prioridade a quem caiu mais e tem menos peso na carteira
    df['Peso'] = (df['Patrimônio'] / total_patrimonio) * 100
    df['Prioridade'] = (df['Valorização %'] * -1) + (100 - df['Peso'])
    
    return df, rentabilidade_ponderada, total_patrimonio
    
