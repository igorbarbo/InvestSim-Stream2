# views/preco_teto.py
import streamlit as st
import pandas as pd
from database.repository import AtivoRepository
from services.teto_service import PrecoTetoService
from services.preco_service import PrecoService
from utils.exportacao import formatar_moeda

def show_preco_teto(user_id):
    st.title("💰 Preço Teto - Método Bazin")
    st.caption("Baseado nos dividendos dos últimos 12 meses")
    
    repo = AtivoRepository()
    teto_service = PrecoTetoService()
    preco_service = PrecoService()
    
    ativos = repo.carregar_por_usuario(user_id)
    if not ativos:
        st.info("Adicione ativos para calcular preço teto.")
        return
    
    col1, col2 = st.columns(2)
    with col1:
        dy = st.slider("📊 Dividend Yield desejado (%)", 4, 12, 6) / 100
        st.caption("6% é o padrão do método Bazin")
    with col2:
        st.metric("DY Selecionado", f"{dy*100:.1f}%")
    
    resultados = []
    for ativo in ativos:
        ticker = ativo['ticker']
        preco_teto, msg = teto_service.calcular_bazin(ticker, dy)
        preco_atual, _, _ = preco_service.get_preco_cached(ticker)
        if preco_teto and preco_atual:
            diff = (preco_teto - preco_atual) / preco_atual * 100
            status = "✅ COMPRAR" if preco_atual <= preco_teto else "⏳ ESPERAR"
            resultados.append({
                "Ticker": ticker,
                "Preço Atual": preco_atual,
                "Preço Teto": preco_teto,
                "Diferença %": diff,
                "Status": status
            })
    
    if resultados:
        df = pd.DataFrame(resultados)
        st.dataframe(
            df.style.format({
                "Preço Atual": lambda x: formatar_moeda(x),
                "Preço Teto": lambda x: formatar_moeda(x),
                "Diferença %": "{:.1f}%"
            }),
            width='stretch'
        )
