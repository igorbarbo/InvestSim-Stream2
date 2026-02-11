import pandas as pd
import yfinance as yf
import streamlit as st

@st.cache_data(ttl=600) # Isso impede o Yahoo de te bloquear por 10 minutos
def sync_prices(df):
    tickers = df['Ativo'].unique().tolist()
    # Puxa os dados uma única vez e guarda na memória
    data = yf.download(tickers, period="1d", progress=False)['Close']
    
    p_dict = {t: float(data[t].iloc[-1] if len(tickers) > 1 else data.iloc[-1]) for t in tickers}
    df['Preço Atual'] = df['Ativo'].map(p_dict)
    df['Patrimônio'] = df['QTD'] * df['Preço Atual']
    df['Valorização %'] = (df['Preço Atual'] / df['Preço Médio'] - 1) * 100
    return df
    
