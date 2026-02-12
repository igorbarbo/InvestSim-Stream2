import streamlit as st
import pandas as pd
import yfinance as yf
import google.generativeai as genai
import gc
from Modules import db, pdf_report # Ajustado para sua pasta no GitHub
import plotly.express as px

# --- SETUP LUXO PRIVATE BANKING ---
st.set_page_config(page_title="Igorbarbo V6 Pro", layout="wide")
db.init_db()

st.markdown("""
    <style>
    .stApp { background-color: #05070A; color: white; }
    .stMetric { background: rgba(255,255,255,0.05); padding: 15px; border-radius: 10px; border-left: 3px solid #D4AF37; }
    h1, h2, h3 { color: #D4AF37 !important; font-family: 'Times New Roman', serif; }
    </style>
    """, unsafe_allow_html=True)

# --- MOTOR DE SIMULAÇÃO ---
def run_simulation(df, aporte):
    total_futuro = df['Patrimônio'].sum() + aporte
    objetivo_cada = total_futuro / len(df)
    sugestoes = []
    for _, row in df.iterrows():
        falta = objetivo_cada - row['Patrimônio']
        if falta > 0:
            sugestoes.append({"Ticker": row['ticker'], "Sugerido (R$)": falta})
    return pd.DataFrame(sugestoes)

# --- INTERFACE ---
menu = st.sidebar.radio("Navegação", ["🏠 Dashboard", "🎯 Simulador de Aporte", "⚙️ Gestão de Ativos", "📄 Relatório PDF"])
df_db = db.get_assets()

if menu == "🏠 Dashboard":
    st.title("💎 Wealth Management Dashboard")
    if not df_db.empty:
        with st.spinner("Sincronizando com Mercado..."):
            tickers = [f"{t}.SA" for t in df_db['ticker']]
            prices = yf.download(tickers, period="1d", progress=False)['Close'].iloc[-1]
            df_db['Preço'] = df_db['ticker'].apply(lambda x: prices.get(f"{x}.SA", 0))
            df_db['Patrimônio'] = df_db['qtd'] * df_db['Preço']
        
        st.metric("Patrimônio Total", f"R$ {df_db['Patrimônio'].sum():,.2f}")
        st.plotly_chart(px.pie(df_db, values='Patrimônio', names='ticker', hole=0.5, color_discrete_sequence=px.colors.sequential.Gold))
        gc.collect()

elif menu == "🎯 Simulador de Aporte":
    st.title("🎯 Estrategista de Capital")
    valor = st.number_input("Valor disponível para aporte (R$)", min_value=0.0, step=100.0)
    if valor > 0 and not df_db.empty:
        sugestoes = run_simulation(df_db, valor)
        st.table(sugestoes)
        if st.button("Consultar IA Advisor"):
            st.info("O Advisor está analisando sua diversificação...")
            # Aqui entraria sua chamada genai.configure...

elif menu == "⚙️ Gestão de Ativos":
    st.subheader("🛠️ Cadastro SQL Persistente")
    with st.form("add_form", clear_on_submit=True):
        t = st.text_input("Ticker (ex: PETR4)").upper()
        q = st.number_input("Quantidade", min_value=0.0)
        p = st.number_input("Preço Médio", min_value=0.0)
        if st.form_submit_button("Salvar no Banco de Dados"):
            db.add_asset(t, q, p)
            st.success(f"Ativo {t} sincronizado!")

elif menu == "📄 Relatório PDF":
    st.title("📄 Relatório de Elite")
    if st.button("Gerar Wealth Report"):
        total = df_db['Patrimônio'].sum() if 'Patrimônio' in df_db else 0
        pdf_bytes = pdf_report.generate(df_db, total, 0)
        st.download_button("Baixar PDF Private", data=pdf_bytes, file_name="Igorbarbo_Wealth_Report.pdf")
        
