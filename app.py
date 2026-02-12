import streamlit as st
import pandas as pd
import yfinance as yf
import gc
from Modules import db, pdf_report 
import plotly.express as px

# --- SETUP INICIAL ---
st.set_page_config(page_title="Igorbarbo Private Wealth", layout="wide")
db.init_db()

# Estilização de Luxo (Ouro sobre Preto)
st.markdown("""
    <style>
    .stApp { background-color: #05070A; color: white; }
    [data-testid="stMetricValue"] { color: #D4AF37 !important; }
    .stProgress > div > div > div > div { background-color: #D4AF37 !important; }
    h1, h2, h3 { color: #D4AF37 !important; font-family: 'serif'; }
    </style>
    """, unsafe_allow_html=True)

# --- ENGINE DA ESTRATÉGIA ---
def run_simulation(df, aporte):
    # Watchlist Híbrida de Elite (Foco > 8% DY)
    hibrida_elite = {'CPLE6': 0.25, 'BBAS3': 0.25, 'KNSC11': 0.25, 'VISC11': 0.25}
    
    sugestoes = []
    if df.empty:
        for ticker, peso in hibrida_elite.items():
            sugestoes.append({"Ativo": ticker, "Sugerido (R$)": f"R$ {aporte * peso:,.2f}", "Motivo": "Montagem de Base"})
    else:
        total_futuro = df['Patrimônio'].sum() + aporte
        objetivo_cada = total_futuro / len(df)
        for _, row in df.iterrows():
            falta = objetivo_cada - row['Patrimônio']
            if falta > 0:
                sugestoes.append({"Ativo": row['ticker'], "Sugerido (R$)": f"R$ {falta:,.2f}", "Motivo": "Equilibrar Carteira"})
    return pd.DataFrame(sugestoes)

# --- NAVEGAÇÃO ---
st.sidebar.title("💎 IGORBARBO V6")
menu = st.sidebar.radio("MENU", ["🏠 Dashboard", "🎯 Aporte Mensal", "⚙️ Gestão", "📄 Relatórios"])
df_db = db.get_assets()

# --- MOTOR DE PREÇOS ---
if not df_db.empty:
    try:
        tickers = [f"{t}.SA" for t in df_db['ticker']]
        prices_data = yf.download(tickers, period="1d", progress=False)['Close']
        if len(tickers) == 1:
            df_db['Preço'] = prices_data.iloc[-1]
        else:
            last_prices = prices_data.iloc[-1]
            df_db['Preço'] = df_db['ticker'].apply(lambda x: last_prices.get(f"{x}.SA", 0))
        df_db['Patrimônio'] = df_db['qtd'] * df_db['Preço']
    except:
        st.sidebar.warning("⚠️ B3 Offline")

# --- TELAS ---
if menu == "🏠 Dashboard":
    st.title("🏛️ Wealth Dashboard")
    if not df_db.empty:
        total_brl = df_db['Patrimônio'].sum()
        renda_mes = total_brl * 0.007 # Estimativa 8% a.a.
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Patrimônio Total", f"R$ {total_brl:,.2f}")
        c2.metric("Renda Mensal Est.", f"R$ {renda_mes:,.2f}")
        c3.metric("Reinvestimento + Aporte", f"R$ {3000 + renda_mes:,.2f}")

        st.write("---")
        # BARRA DE PROGRESSO 100K
        meta = 100000.0
        progresso = min(total_brl / meta, 1.0)
        st.subheader(f"🏆 Progresso R$ 100k: {progresso*100:.1f}%")
        st.progress(progresso)
        st.caption(f"Faltam R$ {max(meta - total_brl, 0.0):,.2f}")

        fig = px.pie(df_db, values='Patrimônio', names='ticker', hole=0.6, 
                     color_discrete_sequence=["#D4AF37", "#C5A028", "#B8860B", "#8B6508"])
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Cadastre seus ativos na aba 'Gestão' para iniciar a bola de neve.")

elif menu == "🎯 Aporte Mensal":
    st.title("🎯 Estrategista de Aporte")
    valor = st.number_input("Valor do Aporte (R$)", value=3000.0, step=100.0)
    if st.button("Calcular Rebalanceamento"):
        sugestoes = run_simulation(df_db, valor)
        st.table(sugestoes)
        st.success("Priorize os ativos acima para manter sua meta de 8% ao ano.")

elif menu == "⚙️ Gestão":
    st.subheader("🛠️ Custódia")
    with st.form("add"):
        t = st.text_input("Ticker").upper()
        q = st.number_input("Qtd", min_value=0.0)
        p = st.number_input("Preço Médio", min_value=0.0)
        if st.form_submit_button("Salvar"):
            db.add_asset(t, q, p)
            st.rerun()

elif menu == "📄 Relatórios":
    st.title("📄 Relatório Private")
    if not df_db.empty:
        if st.button("Gerar PDF"):
            pdf_bytes = pdf_report.generate(df_db, df_db['Patrimônio'].sum(), 0)
            st.download_button("📩 Download PDF", data=pdf_bytes, file_name="Igorbarbo_Report.pdf")
            
