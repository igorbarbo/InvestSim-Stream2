import yfinance as yf
import pandas as pd
import streamlit as st

@st.cache_data(ttl=3600)  # Cache de 1 hora
def get_dados_ativo(ticker, period="1y"):
    """
    Busca dados históricos de ações ou FIIs.
    """
    try:
        ativo = yf.Ticker(ticker)
        dados = ativo.history(period=period)
        return dados
    except Exception as e:
        st.warning(f"Não foi possível obter dados de {ticker}: {e}")
        return pd.DataFrame()
