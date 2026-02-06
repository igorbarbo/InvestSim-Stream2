import streamlit as st
import yfinance as yf

st.title("🔍 Analisador B3 (Ações e FIIs)")

ticker = st.text_input("Digite o Ticker (ex: BBAS3.SA ou HGLG11.SA):", "PETR4.SA").upper()

if st.button("Analisar Ativo"):
    with st.spinner("Acessando dados do Yahoo Finance..."):
        # Versão 0.2.52 lida melhor com tickers da B3
        ativo = yf.Ticker(ticker)
        dados = ativo.history(period="1y")
        
        if not dados.empty:
            st.subheader(f"Desempenho de {ticker} nos últimos 12 meses")
            st.line_chart(dados['Close'])
            
            # Mostra Dividendos se for FII ou Ação pagadora
            dividendos = ativo.dividends
            if not dividendos.empty:
                st.subheader("💰 Proventos Distribuídos")
                st.bar_chart(dividendos.tail(12))
        else:
            st.error("Erro: Dados não encontrados. Verifique se o ticker termina em .SA")
            
