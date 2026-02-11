import pandas as pd
import yfinance as yf

def process_metrics(df):
    """Calcula rentabilidade ponderada (MWA) e motor decisional."""
    df['Preço Atual'] = pd.to_numeric(df['Preço Atual'], errors='coerce')
    df['Preço Médio'] = pd.to_numeric(df['Preço Médio'], errors='coerce')
    df['Patrimônio'] = df['QTD'] * df['Preço Atual']
    
    df['Valorização %'] = (df['Preço Atual'] / df['Preço Médio'] - 1) * 100
    
    total_patrimonio = df['Patrimônio'].sum()
    
    if total_patrimonio > 0:
        # Rentabilidade Ponderada (Real)
        rentabilidade_mwa = (df['Valorização %'] * df['Patrimônio']).sum() / total_patrimonio
        df['Peso'] = (df['Patrimônio'] / total_patrimonio) * 100
    else:
        rentabilidade_mwa = 0
        df['Peso'] = 0

    # Motor de Prioridade: Queda alta + Peso baixo = Prioridade Máxima
    df['Prioridade'] = (df['Valorização %'] * -0.6) + ((100 - df['Peso']) * 0.4)
    
    return df, rentabilidade_mwa, total_patrimonio

def convert_to_usd(valor_brl):
    """Converte BRL para USD usando cotação em tempo real."""
    try:
        usd_ticker = yf.Ticker("USDBRL=X")
        cotacao = usd_ticker.fast_info['last_price']
        return valor_brl / cotacao
    except:
        return valor_brl / 5.60 # Fallback 2026
