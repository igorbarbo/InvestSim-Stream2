import streamlit as st
import pandas as pd
from logic.investment import calcular_investimento, obter_taxa_cenario

st.set_page_config(page_title="InvestSim Pro", layout="wide")
st.title("💰 InvestSim Pro")

col_input, col_output = st.columns([1, 2], gap="large")

with col_input:
    st.subheader("Configurações")
    perfil = st.selectbox("Perfil:", ["Conservador", "Moderado", "Agressivo"])
    taxa_sug = obter_taxa_cenario(perfil)
    
    v_inicial = st.number_input("Inicial (R$)", value=1000.0)
    v_mensal = st.number_input("Mensal (R$)", value=100.0)
    v_taxa = st.slider("Taxa Anual (%)", 1.0, 30.0, taxa_sug)
    v_tempo = st.slider("Anos", 1, 35, 10)

with col_output:
    df = calcular_investimento(v_inicial, v_mensal, v_taxa, v_tempo)
    
    final = df['Patrimônio Total'].iloc[-1]
    investido = df['Total Investido'].iloc[-1]
    
    c1, c2 = st.columns(2)
    c1.metric("Total Acumulado", f"R$ {final:,.2f}")
    c2.metric("Total Investido", f"R$ {investido:,.2f}")
    
    st.line_chart(df.set_index("Mês")[["Patrimônio Total", "Total Investido"]])
    
