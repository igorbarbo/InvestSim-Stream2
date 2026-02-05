import streamlit as st
import pandas as pd
from logic.investment import calcular_investimento

# 1. Configuração da Página
st.set_page_config(page_title="InvestSim Pro", layout="wide")

st.title("💰 Simulador de Investimentos")
st.caption("Acompanhe a evolução do seu patrimônio em tempo real.")

# 2. Criando o Layout em Colunas (Item 1 do nosso plano)
col_input, col_output = st.columns([1, 2], gap="large")

with col_input:
    st.subheader("Configurações")
    # Container para agrupar os inputs visualmente
    with st.container(border=True):
        v_inicial = st.number_input("Investimento Inicial (R$)", value=1000.0, step=500.0)
        v_mensal = st.number_input("Aporte Mensal (R$)", value=100.0, step=50.0)
        v_taxa = st.slider("Taxa Anual (%)", 1.0, 20.0, 10.0)
        v_tempo = st.slider("Tempo (Anos)", 1, 30, 5)

with col_output:
    # Chama a função com o nome correto
    df = calcular_investimento(v_inicial, v_mensal, v_taxa, v_tempo)
    
    # 3. Cards Inteligentes (Item 2 do nosso plano)
    val_final = df['Saldo'].iloc[-1]
    investido = df['Investido'].iloc[-1]
    lucro = val_final - investido

    c1, c2, c3 = st.columns(3)
    c1.metric("Patrimônio Final", f"R$ {val_final:,.2f}")
    c2.metric("Total Investido", f"R$ {investido:,.2f}")
    c3.metric("Ganho em Juros", f"R$ {lucro:,.2f}", delta=f"{(lucro/investido)*100:.1f}%")

    # 4. Gráfico Comparativo (Item 4 do nosso plano)
    st.divider()
    st.write("### Evolução Patrimonial")
    # Mostra tanto o Saldo quanto o que foi Investido para o usuário ver a diferença
    st.line_chart(df.set_index("Mês")[["Saldo", "Investido"]])
    
