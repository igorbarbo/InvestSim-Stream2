import streamlit as st
import pandas as pd
from logic.investment import calcular_investimento, obter_taxa_cenario

# Configuração da Página
st.set_page_config(page_title="InvestSim Pro", layout="wide", page_icon="💰")

st.title("💰 InvestSim Pro")
st.caption("A inteligência financeira para simular o seu futuro.")

# --- 1️⃣ LAYOUT EM COLUNAS ---
col_input, col_output = st.columns([1, 2], gap="large")

with col_input:
    st.subheader("Configurações")
    
    # --- 5️⃣ CENÁRIOS (PERFIS) ---
    perfil = st.selectbox(
        "Selecione seu Perfil de Investimento",
        ["Conservador", "Moderado", "Agressivo"],
        help="Cada perfil sugere uma taxa anual baseada na média do mercado atual."
    )
    
    taxa_sugerida = obter_taxa_cenario(perfil)

    with st.container(border=True):
        v_inicial = st.number_input("Investimento Inicial (R$)", value=1000.0, step=500.0)
        v_mensal = st.number_input("Aporte Mensal (R$)", value=100.0, step=50.0)
        v_taxa = st.slider("Taxa Anual Ajustada (%)", 1.0, 30.0, taxa_sugerida)
        v_tempo = st.slider("Tempo (Anos)", 1, 35, 10)
    
    st.info(f"📌 No cenário **{perfil}**, sua taxa sugerida é de {taxa_sugerida}% ao ano.")

with col_output:
    # Processamento
    df = calcular_investimento(v_inicial, v_mensal, v_taxa, v_tempo)
    
    # --- 2️⃣ CARDS INTELIGENTES ---
    final_val = df['Patrimônio Total'].iloc[-1]
    investido = df['Total Investido'].iloc[-1]
    lucro = final_val - investido

    c1, c2, c3 = st.columns(3)
    c1.metric("Patrimônio Final", f"R$ {final_val:,.2f}", help="Valor total ao fim do prazo.")
    c2.metric("Total Investido", f"R$ {investido:,.2f}", help="Dinheiro que saiu do seu bolso.")
    c3.metric("Rendimento", f"R$ {lucro:,.2f}", delta=f"{(lucro/investido)*100:.1f}% de lucro")

    # --- 4️⃣ GRÁFICO COMPARATIVO ---
    st.divider()
    st.write("### Evolução: Juros Compostos vs. Capital Investido")
    
    chart_data = df.set_index("Mês")[["Patrimônio Total", "Total Investido"]]
    st.line_chart(chart_data, width='stretch')
    
    st.caption("💡 A diferença entre as linhas representa o poder dos juros compostos no tempo.")
    
