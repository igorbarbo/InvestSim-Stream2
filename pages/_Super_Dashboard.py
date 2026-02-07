# pages/_Super_Dashboard.py

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import altair as alt
from io import BytesIO

# Importando funções do utils
from utils.finance_utils import retorno_mensal, volatilidade_anual, max_drawdown, sharpe

# ===============================
# Configuração do app
# ===============================
st.set_page_config(
    page_title="InvestSim — Ultra Ninja",
    page_icon="🦸‍♂️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🦸‍♂️ InvestSim — Ultra Ninja Optimizado")
st.caption("Máximo desempenho para Streamlit Cloud | Bola de Neve • Dividendos Reais • Ranking • Benchmarks")

# ===============================
# Inputs do Usuário
# ===============================
st.sidebar.subheader("Ativos BR & Global")
ativos_input = st.sidebar.text_area(
    "Digite tickers separados por vírgula",
    value="PETR4.SA,VALE3.SA,ITUB4.SA,AAPL,MSFT"
)
ativos_final = [t.strip().upper() for t in ativos_input.split(",") if t.strip()]

anos = st.sidebar.slider("Anos de investimento", 1, 30, 15)
meta_anual = st.sidebar.number_input("Meta anual de patrimônio (R$)", value=500000, step=50000)

st.sidebar.subheader("Aportes Mensais")
aporte_default = [1000]*anos*12
aporte_input = st.sidebar.text_area(
    "Digite aportes mensais separados por vírgula ou deixe padrão",
    value=",".join(map(str, aporte_default))
)
try:
    aportes_mensais = np.array([float(x.strip()) for x in aporte_input.split(",")])
except:
    st.warning("Formato de aporte inválido, usando padrão R$1000/mês")
    aportes_mensais = np.array(aporte_default)

crescimento_div = st.sidebar.slider("Crescimento anual dos dividendos (%)", 0, 15, 8)

# ===============================
# Funções com cache granular
# ===============================
@st.cache_data(ttl=3600)
def get_precos(ticker, period="10y"):
    df = yf.download(ticker, period=period, progress=False)["Adj Close"]
    df.name = ticker
    return df

@st.cache_data(ttl=3600)
def get_dividendos(ticker):
    df = yf.Ticker(ticker).dividends
    df = df.resample('M').sum().fillna(0)
    df.name = ticker
    return df

# ===============================
# Baixar dados
# ===============================
if not ativos_final:
    st.warning("Digite pelo menos um ativo válido!")
    st.stop()

df_preco = pd.concat([get_precos(t) for t in ativos_final], axis=1).fillna(method="ffill")
df_div = pd.concat([get_dividendos(t) for t in ativos_final], axis=1)

df_preco = df_preco.resample('M').last()
df_div = df_div.resample('M').sum()
meses = anos*12
df_preco = df_preco.iloc[:meses]
df_div = df_div.iloc[:meses]

# ===============================
# Simulação Ultra Ninja vetorizada
# ===============================
aporte_array = np.pad(aportes_mensais, (0, meses - len(aportes_mensais)), 'edge')
patrimonio = np.cumsum(aporte_array)
dividendos = df_div.values.cumsum(axis=0)
carteira = patrimonio[:,None] + dividendos
carteira_total = carteira.sum(axis=1)

df_carteira = pd.DataFrame({
    "Mês": range(1, meses+1),
    "Carteira": carteira_total,
    "Dividendo": dividendos.sum(axis=1)
})
df_carteira["Ano"] = (df_carteira["Mês"]-1)//12 + 1
df_carteira["Meta"] = df_carteira["Ano"] * meta_anual
df_carteira["Status"] = np.where(df_carteira["Carteira"] >= df_carteira["Meta"], "Acima da Meta", "Abaixo da Meta")

# Ranking de contribuições
df_ranking = pd.DataFrame(df_div.sum().sort_values(ascending=False))
df_ranking.columns = ["Contribuição Total"]

# ===============================
# KPIs
# ===============================
st.subheader("📊 KPIs Ultra Ninja")
c1, c2, c3, c4 = st.columns(4)
c1.metric("💼 Patrimônio Final", f"R$ {df_carteira['Carteira'].iloc[-1]:,.0f}")
c2.metric("💸 Dividendos Totais", f"R$ {df_carteira['Dividendo'].sum():,.0f}")
c3.metric("📊 Nº de Ativos", len(ativos_final))
c4.metric("🔥 Yield Médio", f"{df_carteira['Dividendo'].sum()/df_carteira['Carteira'].iloc[-1]*100:.2f}%")
st.divider()

# ===============================
# Gráfico Bola de Neve otimizado
# ===============================
st.subheader("❄️ Bola de Neve Ultra Ninja")
df_plot = df_carteira.iloc[::3] if meses > 360 else df_carteira

cores = alt.condition(
    alt.datum.Status == "Acima da Meta",
    alt.value("green"),
    alt.value("red")
)
linha = alt.Chart(df_plot).mark_line(point=True).encode(
    x="Mês:O",
    y="Carteira:Q",
    color=cores,
    tooltip=["Mês","Ano","Carteira","Meta","Status","Dividendo"]
)
meta_line = alt.Chart(df_plot).mark_line(strokeDash=[5,5], color="blue").encode(
    x="Mês:O",
    y="Meta:Q",
    tooltip=["Meta"]
)
st.altair_chart(linha + meta_line, use_container_width=True)

# ===============================
# Comparativo SP500 / IBOV otimizado
# ===============================
st.subheader("📈 Comparativo com Benchmarks")
sp500 = get_precos("^GSPC").iloc[:meses]
ibov = get_precos("^BVSP").iloc[:meses]
df_comp = pd.DataFrame({
    "Carteira": df_carteira["Carteira"],
    "S&P500": sp500.values / sp500.values[0] * df_carteira["Carteira"].iloc[0],
    "IBOV": ibov.values / ibov.values[0] * df_carteira["Carteira"].iloc[0]
})
st.line_chart(df_comp)

# ===============================
# Heatmap e Ranking otimizado
# ===============================
st.subheader("🔥 Heatmap de Preços")
df_heat = df_preco.reset_index().melt(id_vars="Date", var_name="Ativo", value_name="Preço")
heat = alt.Chart(df_heat).mark_rect().encode(
    x="Date:T",
    y="Ativo:N",
    color=alt.Color("Preço:Q", scale=alt.Scale(scheme="greens")),
    tooltip=["Ativo","Date","Preço"]
)
st.altair_chart(heat, use_container_width=True)

st.subheader("💰 Ranking de Contribuições")
st.dataframe(df_ranking.style.format({"Contribuição Total":"R$ {:,.2f}"}))

# ===============================
# KPIs de risco
# ===============================
vol = volatilidade_anual(df_preco.sum(axis=1))
dd = max_drawdown(df_preco.sum(axis=1))
sh = sharpe(df_preco.sum(axis=1))

c1, c2, c3 = st.columns(3)
c1.metric("📉 Volatilidade Anual", f"{vol:.2f}")
c2.metric("📉 Max Drawdown", f"{dd:.2%}")
c3.metric("⚖️ Sharpe Ratio", f"{sh:.2f}")
if dd < -0.2: st.warning(f"⚠️ Alto Drawdown: {dd:.2%}")

# ===============================
# Exportação PDF apenas com Altair
# ===============================
st.subheader("📄 Exportar Relatório (CSV/Excel)")
if st.button("Exportar CSV"):
    st.download_button(
        label="Download CSV",
        data=df_carteira.to_csv(index=False).encode('utf-8'),
        file_name="InvestSim_Ultra_Ninja.csv",
        mime="text/csv"
    )
if st.button("Exportar Excel"):
    st.download_button(
        label="Download Excel",
        data=df_carteira.to_excel(index=False, engine='openpyxl'),
        file_name="InvestSim_Ultra_Ninja.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

st.markdown("---")
st.caption("InvestSim — Ultra Ninja Optimizado | Deploy seguro no Streamlit Cloud")
