import streamlit as st

# Configuração da página
st.set_page_config(
    page_title="InvestSim - Simulador de Investimentos",
    page_icon="💰",
    layout="wide"
)

# Título Principal
st.title("💰 InvestSim: Seu Futuro Financeiro")

st.markdown("""
Bem-vindo ao **InvestSim**! 
Use o menu lateral para navegar entre as ferramentas:
* **Simulador de Juros Compostos:** Planeje sua liberdade financeira.
* **Análise de Ativos:** Veja o histórico real de preços (via yfinance).
* **Minha Carteira:** Monte sua alocação estratégica.
""")

st.divider()

# Exemplo de uso rápido da sua UTILS na Home
from utils.simulator import simulate_investment

st.subheader("🚀 Simulação Rápida (Aporte Único)")
col1, col2 = st.columns(2)

with col1:
    valor_init = st.number_input("Quanto você tem hoje? (R$)", value=1000)
    tempo = st.slider("Quantos meses vai deixar rendendo?", 1, 360, 60)

with col2:
    taxa = st.number_input("Taxa de juros anual (%)", value=10.0)
    df = simulate_investment(valor_init, 0, tempo, taxa)
    
    patrimonio_final = df['Patrimônio'].iloc[-1]
    st.metric("Patrimônio Final Estimado", f"R$ {patrimonio_final:,.2f}")

st.line_chart(df.set_index("Mês"))
