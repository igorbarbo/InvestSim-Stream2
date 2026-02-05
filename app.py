import streamlit as st
import pandas as pd
# Importando suas funções utilitárias
from utils.simulator import simulate_investment

# 1. Configuração da Página
st.set_page_config(page_title="InvestSim Pro", page_icon="💰", layout="wide")

# Custom CSS para melhorar o visual no mobile
st.markdown("""
    <style>
    .main { padding-top: 1rem; }
    .stMetric { background-color: #f8f9fa; padding: 15px; border-radius: 10px; border: 1px solid #eee; }
    </style>
    """, unsafe_allow_html=True)

# 2. Cabeçalho
st.title("💰 InvestSim: Simulador de Patrimônio Real")
st.markdown("Analise seu crescimento descontando a inflação e comparando cenários.")

# 3. Entradas de Dados (Parâmetros)
with st.container():
    st.subheader("⚙️ Parâmetros da Simulação")
    col_in1, col_in2, col_in3, col_in4 = st.columns(4)
    
    with col_in1:
        val_inicial = st.number_input("Investimento Inicial (R$)", min_value=0.0, value=1000.0, step=500.0)
    with col_in2:
        aporte_mensal = st.number_input("Aporte Mensal (R$)", min_value=0.0, value=200.0, step=50.0)
    with col_in3:
        taxa_anual = st.number_input("Rentabilidade Anual (%)", min_value=0.0, value=10.0, step=0.5)
    with col_in4:
        inflacao_anual = st.number_input("Inflação Anual (%)", min_value=0.0, value=4.5, step=0.1)

    anos = st.slider("Tempo de Investimento (Anos)", 1, 40, 10)
    meses = anos * 12

st.divider()

# 4. Cálculos Matemáticos (Melhoria 3: Subtração da Inflação)
# Taxa Real (Equação de Fisher): ((1 + i) / (1 + f)) - 1
taxa_real_anual = ((1 + taxa_anual/100) / (1 + inflacao_anual/100) - 1) * 100

# Simulação Nominal (Sem inflação)
df_nominal = simulate_investment(val_inicial, aporte_mensal, meses, taxa_anual)
# Simulação Real (Com subtração da inflação)
df_real = simulate_investment(val_inicial, aporte_mensal, meses, taxa_real_anual)

# 5. Dashboard de Resultados
if not df_nominal.empty:
    # Dados para métricas
    total_nominal = df_nominal['Patrimônio'].iloc[-1]
    total_real = df_real['Patrimônio'].iloc[-1]
    investido_total = val_inicial + (aporte_mensal * meses)
    lucro_juros = total_nominal - investido_total

    # Exibição de Métricas
    m1, m2, m3 = st.columns(3)
    m1.metric("💰 Patrimônio Bruto", f"R$ {total_nominal:,.2f}")
    m2.metric("🏦 Poder de Compra (Real)", f"R$ {total_real:,.2f}", 
              delta=f"R$ {total_real - total_nominal:,.2f} (Perda Inflacionária)", delta_color="inverse")
    m3.metric("📈 Ganho em Juros", f"R$ {lucro_juros:,.2f}")

    st.write("")

    # 6. Visualização Gráfica (Melhoria 1 e 2: Comparação de Cenários)
    st.subheader("📊 Comparação: Valor Nominal vs. Poder de Compra")
    
    # Preparando dados para o gráfico
    grafico_data = pd.DataFrame({
        "Mês": df_nominal["Mês"],
        "Valor Nominal (Sem Inflação)": df_nominal["Patrimônio"],
        "Valor Real (Descontando Inflação)": df_real["Patrimônio"]
    }).set_index("Mês")
    
    st.area_chart(grafico_data, color=["#1c3d5a", "#29b5e8"])
    
    st.info(f"💡 Em {anos} anos, a inflação de {inflacao_anual}% 'comerá' aproximadamente R$ {total_nominal - total_real:,.2f} do seu poder de compra.")

    # 7. Tabela Detalhada
    with st.expander("📄 Ver tabela comparativa mensal"):
        df_comp = df_nominal.copy()
        df_comp['Patrimônio Real'] = df_real['Patrimônio']
        st.dataframe(df_comp.style.format("R$ {:,.2f}"), use_container_width=True)

else:
    st.error("Erro ao gerar simulação. Verifique os parâmetros.")

st.sidebar.markdown("### 🚀 InvestSim Pro")
st.sidebar.info("Este simulador utiliza a Taxa Real para calcular quanto seu dinheiro valerá no futuro em preços de hoje.")
