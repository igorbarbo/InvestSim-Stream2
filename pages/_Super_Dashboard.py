import streamlit as st
from logic.market_data import get_dados_ativo
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

st.subheader("🌎 Super Dashboard de Ativos")

tickers = st.text_area("Digite os tickers separados por vírgula", value="PETR4.SA,BOVA11,KNRI11,VNQ").split(",")

dfs = {}
for t in tickers:
    t = t.strip()
    df = get_dados_ativo(t)
    if not df.empty:
        dfs[t] = df["Close"]

if dfs:
    df_concat = pd.DataFrame(dfs)
    st.line_chart(df_concat)

    # Heatmap de dividendos (exemplo com variação diária)
    corr = df_concat.pct_change().corr()
    fig, ax = plt.subplots()
    sns.heatmap(corr, annot=True, cmap="coolwarm", ax=ax)
    st.pyplot(fig)
