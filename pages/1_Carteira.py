import streamlit as st
import pandas as pd
from logic.investment import calcular_investimento, obter_taxa_cenario


# ===============================
# CONFIGURAÇÃO DA PÁGINA
# ===============================
st.set_page_config(
    page_title="Carteira",
    layout="wide"
)

st.title("📊 Carteira de Investimentos")


# ===============================
# SESSION STATE
# ===============================
if "perfil" not in st.session_state:
    st.session_state.perfil = "Conservador"

if "taxa" not in st.session_state:
    st.session_state.taxa = obter_taxa_cenario(st.session_state.perfil)


# ===============================
# FUNÇÃO DE ATUALIZAÇÃO
# ===============================
def atualizar_taxa():
    st.session_state.taxa = obter_taxa_cenario(st.session_state.perfil)


# ===============================
# CONTROLES
# ===============================
st.selectbox(
    "Perfil:",
    options=["Conservador", "Moderado", "Agressivo"],
    key="perfil",
    on_change=atualizar_taxa
)

st.slider(
    "Taxa Anual (%)",
    min_value=1.0,
    max_value=30.0,
    step=0.1,
    key="taxa"
)

v_inicial = st.number_input(
    "Inicial (R$)",
    value=1000.0,
    min_value=0.0,
    step=100.0
)

v_mensal = st.number_input(
    "Mensal (R$)",
    value=100.0,
    min_value=0.0,
    step=50.0
)

v_tempo = st.slider(
    "Anos",
    min_value=1,
    max_value=35,
    value=10
)


# ===============================
# CÁLCULO
# ===============================
df = calcular_investimento(
    inicial=v_inicial,
    mensal=v_mensal,
    taxa_anual=st.session_state.taxa,
    anos=v_tempo
)

if df is None or df.empty:
    st.warning("Não foi possível calcular o investimento.")
    st.stop()


# ===============================
# PADRONIZAÇÃO (SEM ACENTOS)
# ===============================
df = df.rename(columns={
    "Mês": "Mes",
    "Patrimônio Total": "Patrimonio Total"
})


# ===============================
# MÉTRICAS
# ===============================
final = float(df["Patrimonio Total"].iloc[-1])
investido = float(df["Total Investido"].iloc[-1])
ganho = final - investido

c1, c2, c3 = st.columns(3)

c1.metric("Total Acumulado", f"R$ {final:,.2f}")
c2.metric("Total Investido", f"R$ {investido:,.2f}")
c3.metric(
    "Ganho Total",
    f"R$ {ganho:,.2f}",
    delta=f"{(ganho / investido) * 100:.1f}%" if investido > 0 else None
)


# ===============================
# GRÁFICO
# ===============================
df_chart = (
    df.sort_values("Mes")
      .set_index("Mes")[["Patrimonio Total", "Total Investido"]]
)

st.line_chart(df_chart)
