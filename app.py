import streamlit as st
import pandas as pd
# Importando as funções da sua pasta utils
try:
    from utils.simulator import simulate_investment
except ImportError:
    st.error("Erro ao carregar a pasta 'utils'. Verifique se o arquivo __init__.py existe.")
    st.stop()

# 1. Configuração da Página
st.set_page_config(
    page_title="InvestSim - Dashboard",
    page_icon="💰",
    layout="wide"
)

# Estilo CSS para remover o excesso de espaço no topo
st.markdown("<style>div.block-container{padding-top:2rem;}</style>", unsafe_allow_html=True)

# 2. Título e Descrição
st.title("💰 InvestSim: Seu Futuro Financeiro")
st.markdown("Transforme sua estratégia de aportes em uma visualização profissional.")

st.divider()

# 3. Sidebar (Parâmetros)
st.sidebar.header("⚙️ Configurações")
val_inicial = st.sidebar.number_input("Quanto você tem hoje? (R$)", min_value=0.0, value=1000.0, step=500.0)
aporte_mensal = st.sidebar.number_input("Aporte Mensal (R$)", min_value=0.0, value=200.0, step=50.0)
anos = st.sidebar.slider("Tempo de investimento (Anos)", 1, 40, 10)
taxa_anual = st.sidebar.number_input("Taxa de Juros Anual (%)", min_value=0.0, value=10.0, step=0.5)

meses = anos * 12

# 4. Processamento dos Dados
df = simulate_investment(val_inicial, aporte_mensal, meses, taxa_anual)

# 5. Dashboard Visual
if not df.empty:
    # Cálculos para as métricas
    total_final = df['Patrimônio'].iloc[-1]
    total_investido = val_inicial + (aporte_mensal * meses)
    juros_ganhos = total_final - total_investido

    # Exibição de Métricas em Cards
    m1, m2, m3 = st.columns(3)
    m1.metric("💰 Patrimônio Total", f"R$ {total_final:,.2f}")
    m2.metric("🏦 Total Investido", f"R$ {total_investido:,.2f}")
    m3.metric("📈 Ganho em Juros", f"R$ {juros_ganhos:,.2f}", delta=f"{((juros_ganhos/total_investido)*100):.1f}%")

    st.write("") # Espaçamento

    # Gráfico de Área Profissional
    st.subheader("📊 Evolução do Patrimônio ao Longo do Tempo")
    
    # Criamos um gráfico de área que é visualmente superior à tabela
    st.area_chart(df.set_index("Mês")["Patrimônio"], color="#29b5e8")

    # 6. Tabela Detalhada (Escondida por padrão para não ficar "terrível")
    with st.expander("📄 Ver detalhes da evolução mensal (Tabela)"):
        # Formatando a tabela para exibição elegante
        df_formatado = df.copy()
        df_formatado['Patrimônio'] = df_formatado['Patrimônio'].map('R$ {:,.2f}'.format)
        st.dataframe(df_formatado, use_container_width=True)

    # 7. Botão de Download
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Baixar Dados da Simulação (CSV)",
        data=csv,
        file_name='simulacao_investsim.csv',
        mime='text/csv',
    )

else:
    st.warning("Aguardando parâmetros para gerar a simulação.")

st.sidebar.markdown("---")
st.sidebar.caption("InvestSim v1.0 - Criado para fins educacionais.")
