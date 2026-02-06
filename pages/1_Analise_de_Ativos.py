import streamlit as st
import yfinance as yf

st.set_page_config(page_title="Análise", layout="wide")
st.title("🔍 Análise de Ativos")

ticker = st.text_input("Digite o ticker (ex: PETR4.SA):", "VALE3.SA").upper()

if st.button("Buscar Dados"):
    with st.spinner("Consultando Yahoo Finance..."):
        dados = yf.Ticker(ticker).history(period="1y")
        if not dados.empty:
            st.line_chart(dados['Close'])
            preco_atual = dados['Close'].iloc[-1]
            st.metric("Preço Atual", f"R$ {preco_atual:.2f}")
        else:
            st.error("Ticker não encontrado. Verifique se usou o sufixo .SA")
            
