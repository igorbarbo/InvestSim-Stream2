import yfinance as yf
import pandas as pd
import streamlit as st

def run_backtest(df_carteira):
    """Compara o desempenho da carteira com o Ibovespa no último ano."""
    tickers = [f"{t}.SA" if not t.endswith(".SA") else t for t in df_carteira['Ativo'].tolist()]
    
    try:
        # Busca dados do último ano
        data = yf.download(tickers + ["^BVSP"], period="1y", interval="1d")['Close']
        retornos = data.pct_change().dropna()
        acumulado = (1 + retornos).cumprod()
        
        # Performance da Carteira (Média ponderada simplificada dos ativos)
        colunas_ativos = [c for c in acumulado.columns if c != "^BVSP"]
        carteira_nomalizada = acumulado[colunas_ativos].mean(axis=1)
        ibov_normalizado = acumulado["^BVSP"]
        
        return pd.DataFrame({
            "Minha Carteira": carteira_nomalizada,
            "Ibovespa": ibov_normalizado
        })
    except Exception as e:
        st.error(f"Erro no Backtesting: {e}")
        return None
      
