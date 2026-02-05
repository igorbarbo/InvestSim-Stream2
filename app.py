import streamlit as st
import pandas as pd
# Aqui está o segredo: o caminho deve ser logic.investment
from logic.investment import calcular_investimento

st.set_page_config(page_title="InvestSim Pro", layout="wide")

st.title("💰 Simulador de Investimentos")

# Layout em Colunas
col_input, col_output = st.columns([1, 2], gap="large")

with col_input:
    st.subheader("Configurações")
    with st.container(border=True):
        v_inicial = st.number_input("Investimento Inicial (R$)", value=1000.0)
        v_mensal = st.number_input("Aporte Mensal (R$)", value=100.0)
        v_taxa = st.slider("Taxa Anual (%)", 1.0, 20.0, 10.0)
        v_tempo = st.slider("Tempo (Anos)", 1, 30, 5)

with col_output:
    # Chama a função que criamos na pasta logic
    df = calcular_investimento(v_inicial, v_mensal, v_taxa, v_tempo)
    
    # Cards Profissionais
    final_val = df['Saldo'].iloc[-1]
    investido = df['Investido'].iloc[-1]
    lucro = final_val - investido

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Acumulado", f"R$ {final_val:,.2f}")
    c2.metric("Total Investido", f"R$ {investido:,.2f}")
    c3.metric("Rendimento", f"R$ {lucro:,.2f}", delta=f"{(lucro/investido)*100:.1f}%")

    st.divider()
    # Gráfico com as duas linhas (Saldo vs Investido)
    st.line_chart(df.set_index("Mês")[["Saldo", "Investido"]])
    
