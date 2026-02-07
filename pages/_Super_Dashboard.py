import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(page_title="Super Dashboard", layout="wide")

st.title("🚀 Super Dashboard de Investimentos")
st.caption("Ações Brasileiras • Ações Globais • FIIs • Bola de Neve de Dividendos")

# =========================
# DADOS DE EXEMPLO (BASE)
# =========================

dados = pd.DataFrame({
    "Ativo": [
        "PETR4", "VALE3", "ITUB4",
        "AAPL", "MSFT",
        "MXRF11", "HGLG11", "KNRI11"
    ],
    "Categoria": [
        "Ação BR", "Ação BR", "Ação BR",
        "Ação Global", "Ação Global",
        "FII", "FII", "FII"
    ],
    "Dividendos_Ano": [
        1800, 1200, 950,
        400, 350,
        2100, 2400, 1950
    ],
    "Patrimonio": [
        22000, 18000, 15000,
        26000, 24000,
        30000, 35000, 28000
    ]
})

# =========================
# KPIs
# =========================

col1, col2, col3, col4 = st.columns(4)

col1.metric("💼 Patrimônio Total", f"R$ {dados['Patrimonio'].sum():,.0f}")
col2.metric("💸 Dividendos Anuais", f"R$ {dados['Dividendos_Ano'].sum():,.0f}")
col3.metric("📊 Nº de Ativos", dados.shape[0])
col4.metric("🔥 Yield Médio", f"{(dados['Dividendos_Ano'].sum() / dados['Patrimonio'].sum())*100:.2f}%")

st.divider()

# =========================
# GRÁFICO DE PATRIMÔNIO
# =========================

st.subheader("📈 Patrimônio por Ativo")

chart_patrimonio = (
    alt.Chart(dados)
    .mark_bar()
    .encode(
        x=alt.X("Ativo:N", sort="-y"),
        y="Patrimonio:Q",
        color="Categoria:N",
        tooltip=["Ativo", "Patrimonio", "Categoria"]
    )
)

st.altair_chart(chart_patrimonio, use_container_width=True)

# =========================
# DIVIDENDOS POR CATEGORIA
# =========================

st.subheader("💰 Dividendos por Categoria")

div_categoria = (
    alt.Chart(dados)
    .mark_bar()
    .encode(
        x="Categoria:N",
        y="sum(Dividendos_Ano):Q",
        color="Categoria:N",
        tooltip=["sum(Dividendos_Ano)"]
    )
)

st.altair_chart(div_categoria, use_container_width=True)

# =========================
# HEATMAP DE DIVIDENDOS
# =========================

st.subheader("🔥 Heatmap de Dividendos")

heatmap = (
    alt.Chart(dados)
    .mark_rect()
    .encode(
        x="Ativo:N",
        y="Categoria:N",
        color=alt.Color(
            "Dividendos_Ano:Q",
            scale=alt.Scale(scheme="greens")
        ),
        tooltip=["Ativo", "Dividendos_Ano"]
    )
    .properties(height=300)
)

st.altair_chart(heatmap, use_container_width=True)

# =========================
# BOLA DE NEVE (SIMULAÇÃO)
# =========================

st.subheader("❄️ Bola de Neve de Dividendos")

anos = st.slider("Horizonte de investimento (anos)", 1, 30, 10)
aporte_anual = st.number_input("Aporte anual (R$)", value=12000, step=1000)
taxa_reinvestimento = st.slider("Reinvestimento dos dividendos (%)", 0, 100, 100)

patrimonio = dados["Patrimonio"].sum()
dividendos = dados["Dividendos_Ano"].sum()

historico = []

for ano in range(1, anos + 1):
    reinvestido = dividendos * (taxa_reinvestimento / 100)
    patrimonio += reinvestido + aporte_anual
    dividendos *= 1.08  # crescimento médio dos dividendos
    historico.append({
        "Ano": ano,
        "Patrimônio": patrimonio
    })

df_bola = pd.DataFrame(historico)

st.line_chart(df_bola.set_index("Ano"))

# =========================
# TABELA FINAL
# =========================

st.subheader("📋 Resumo dos Ativos")

st.dataframe(
    dados.sort_values("Dividendos_Ano", ascending=False),
    use_container_width=True
)

st.success("✅ Dashboard carregado com sucesso — 100% compatível com Streamlit Cloud")
