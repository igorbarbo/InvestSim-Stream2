import yfinance as yf
import pandas as pd
import numpy as np

def buscar_dados_historicos(ticker):
    try:
        acao = yf.Ticker(f"{ticker}.SA")
        hist = acao.history(period="5y")
        return hist if not hist.empty else None
    except:
        return None

def analisar_preco_ativo(ticker, hist):
    if hist is None:
        return "🔵 DADOS INSUFICIENTES", "#808080", "Sem histórico para análise.", 0
    
    preco_atual = hist['Close'].iloc[-1]
    media_12m = hist['Close'].tail(252).mean()
    p20 = np.percentile(hist['Close'], 20)
    p80 = np.percentile(hist['Close'], 80)
    
    if preco_atual <= p20:
        return "🟢 OPORTUNIDADE!", "#00FF00", f"Preço entre os 20% mais baixos dos últimos 5 anos.", 100
    elif preco_atual >= p80:
        return "🔴 CARO!", "#FF4444", f"Próximo das máximas históricas. Evite comprar agora.", 20
    elif preco_atual < media_12m:
        return "🟢 BARATO", "#7FFF00", "Abaixo da média do último ano.", 70
    else:
        return "🟡 NEUTRO", "#D4AF37", "Preço justo perante a média.", 50

def calcular_bazin(ticker):
    try:
        acao = yf.Ticker(f"{ticker}.SA")
        dividendos = acao.dividends.tail(12).sum()
        preco_teto = dividendos / 0.06 # Base 6% a.a.
        return preco_teto
    except:
        return 0
        
