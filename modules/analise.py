import yfinance as yf
import numpy as np
import streamlit as st

@st.cache_data(ttl=3600)
def pegar_preco(ticker):
    """Obtém o preço atual de fechamento via Yahoo Finance."""
    try:
        t = yf.Ticker(f"{ticker}.SA")
        return t.history(period="1d")['Close'].iloc[-1]
    except:
        return None

def analisar_preco_ativo(ticker):
    """Executa a análise Caro/Barato baseada em percentis históricos de 5 anos."""
    try:
        t = yf.Ticker(f"{ticker}.SA")
        hist = t.history(period="5y")
        if hist.empty: return "🔵 SEM DADOS", "#808080", "Ticker não encontrado.", 0
        
        atual = hist['Close'].iloc[-1]
        p20 = np.percentile(hist['Close'], 20)
        p80 = np.percentile(hist['Close'], 80)

        if atual <= p20:
            return "🟢 OPORTUNIDADE!", "#00FF00", "Preço em zona de acumulação (Percentil 20).", 100
        elif atual >= p80:
            return "🔴 CARO!", "#FF4444", "Preço em zona de euforia (Percentil 80). Cuidado.", 20
        return "🟡 NEUTRO", "#D4AF37", "Preço em zona de equilíbrio histórico.", 50
    except:
        return "🔵 ERRO", "#808080", "Falha na conexão com o mercado.", 0
      
