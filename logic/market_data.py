import streamlit as st
import yfinance as yf
import pandas as pd

@st.cache_data(ttl=3600)
def get_dados_ativo(ticker: str) -> pd.DataFrame:
    try:
        ticker = ticker.upper()
        if not ticker.endswith(".SA"):
            ticker = ticker + ".SA"

        ativo = yf.Ticker(ticker)
        dados = ativo.history(period="1y")

        if dados.empty:
            return pd.DataFrame()

        return dados

    except Exception:
        return pd.DataFrame()
