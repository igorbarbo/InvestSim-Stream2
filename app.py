import streamlit as st
import pandas as pd
from utils.simulator import simulate_investment

# 1. Configuração da Página para Mobile e Desktop
st.set_page_config(
    page_title="InvestSim Pro",
    page_icon="💰",
    layout="wide"
)

# Estilo para melhorar a visualização em telas pequenas
st.markdown("""
    <style>
    .main { padding-top: 1rem; }
    .stMetric { background-color: #f0f2f6; padding: 15px; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# 2. Título Principal
st.title("💰 InvestSim: Seu Futuro Financeiro")
st.markdown("Visualize o poder dos juros compostos no seu patrimônio.")

st.divider()

# 3. Entradas de Dados (Otimizadas para não sumirem)
st.subheader("⚙️ Parâmetros da Simulação")
col_in1, col_in2, col_in3 = st.columns([1, 1, 1])

with col_in1:
    val_inicial = st.number_input("Investimento Inicial (R$)", min_value=0.0, value=1000.0, step=500.0)
with col_in2:
    aporte_mensal = st.number_input("Aporte Mensal (R$)", min_value=0.0, value=200.0, step=50.0)
with col_in3:
    taxa_anual = st.number_input("Juros Anual (%)", min_value=0.0, value=10.0, step=0.5)

anos = st.slider("Tempo de investimento (Anos)", 1, 40, 10)
meses = anos * 12

st.divider()

# 4. Processamento de Dados com Lógica de Comparação
df = simulate_investment(val_inicial, aporte_mensal, meses, taxa_anual)

if not df.empty:
    # Criando as camadas para o gráfico empilhado
    df['Total Investido'] = val_inicial + (df['Mês'] * aporte_mensal)
    df['Juros Acumulados'] = df['Patrimônio'] - df['Total Investido']
    
    # 5. Dashboard de Métricas
    total_final = df['Patrimônio'].iloc[-1]
    investido_total = df['Total Investido'].iloc[-1]
    juros_total = df['Juros Acumulados'].iloc[-1]
    
    m1, m2, m3 = st.columns(3)
    m1.metric("💰 Patrimônio Final", f"R$ {total_final:,.2f}")
    m2.metric("🏦 Capital Investido", f"R$ {investido_total:,.2f}")
    m3.metric("📈 Total em Juros", f"R$ {juros_total:,.2f}", 
              delta=f"{((juros_total/investido_total)*100):.1f}% do esforço")

    st.write("")

    # 6. Gráfico de Área Empilhada (Visualização Premium)
    st.subheader("📊 Composição do Patrimônio")
    st.markdown("Veja como os juros (em azul claro) começam a superar seu aporte com o tempo.")
    
    # Preparando dados para o gráfico
    chart_data = df.set_index("Mês")[['Total Investido', 'Juros Acumulados']]
    st.area_chart(chart_data, color=["#29b5e8", "#1c3d5a"])

    # 7. Tabela Detalhada (Organizada)
    with st.expander("📄 Ver Planilha Mensal Detalhada"):
        df_display = df.copy()
        for col in ['Patrimônio', 'Total Investido', 'Juros Acumulados']:
            df_display[col] = df_display[col].map('R$ {:,.2f}'.format)
        st.dataframe(df_display, use_container_width=True)

    # 8. Download dos Dados
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Baixar Simulação em CSV",
        data=csv,
        file_name='investsim_resultados.csv',
        mime='text/csv',
    )
else:
    st.warning("Ajuste os valores para visualizar a simulação.")

st.caption("InvestSim v2.0 - O poder do tempo a seu favor.")
