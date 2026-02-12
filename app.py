import streamlit as st
import pandas as pd
import yfinance as yf
import gc
from Modules import db, pdf_report 
import plotly.express as px

st.set_page_config(page_title="Igorbarbo V6 Pro", layout="wide")
db.init_db()

st.markdown("""
    <style>
    .stApp { background-color: #05070A; color: white; }
    [data-testid="stMetricValue"] { color: #D4AF37 !important; }
    .stProgress > div > div > div > div { background-color: #D4AF37 !important; }
    h1, h2, h3 { color: #D4AF37 !important; font-family: 'serif'; }
    </style>
    """, unsafe_allow_html=True)

# --- NAVEGAÇÃO ---
st.sidebar.title("💎 IGORBARBO PRIVATE")
menu = st.sidebar.radio("MENU", ["🏠 Dashboard", "🎯 Projeção & Disciplina", "⚙️ Gestão", "📄 PDF"])
df_db = db.get_assets()

# --- PREÇOS ---
if not df_db.empty:
    try:
        tickers = [f"{t}.SA" for t in df_db['ticker']]
        prices = yf.download(tickers, period="1d", progress=False)['Close']
        if len(tickers) == 1:
            df_db['Preço'] = prices.iloc[-1]
        else:
            last_p = prices.iloc[-1]
            df_db['Preço'] = df_db['ticker'].apply(lambda x: last_p.get(f"{x}.SA", 0))
        df_db['Patrimônio'] = df_db['qtd'] * df_db['Preço']
    except: st.sidebar.warning("B3 Offline")

# --- DASHBOARD ---
if menu == "🏠 Dashboard":
    st.title("🏛️ Wealth Portfolio")
    if not df_db.empty:
        total = df_db['Patrimônio'].sum()
        renda = total * 0.0083
        c1, c2, c3 = st.columns(3)
        c1.metric("Patrimônio Total", f"R$ {total:,.2f}")
        c2.metric("Salário Mensal (10% aa)", f"R$ {renda:,.2f}")
        c3.metric("Próximo Aporte", f"R$ {3000 + renda:,.2f}")
        
        st.write("---")
        prog = min(total / 100000, 1.0)
        st.subheader(f"🏆 Rumo aos R$ 100k: {prog*100:.1f}%")
        st.progress(prog)
        
        fig = px.pie(df_db, values='Patrimônio', names='ticker', hole=0.6,
                     color_discrete_sequence=["#D4AF37", "#C5A028", "#B8860B"])
        st.plotly_chart(fig, use_container_width=True)
    else: st.info("Adicione ativos na aba Gestão.")

# --- PROJEÇÃO & CHOQUE DE REALIDADE ---
elif menu == "🎯 Projeção & Disciplina":
    st.title("🚀 Simulador de Futuro")
    anos = st.slider("Anos de investimento", 1, 30, 10)
    taxa = 0.0083 # 10% aa
    aporte = 3000
    
    # Cálculo COM reinvestimento
    meses = anos * 12
    df_p = pd.DataFrame({'Mes': range(1, meses+1)})
    df_p['Com Reinvestimento'] = [aporte * (((1+taxa)**m - 1)/taxa) for m in df_p['Mes']]
    
    # Cálculo SEM reinvestimento (Gasto dos dividendos)
    df_p['Sem Reinvestimento'] = [aporte * m for m in df_p['Mes']]
    
    st.subheader("O Custo de Gastar os Dividendos")
    fig_comp = px.line(df_p, x='Mes', y=['Com Reinvestimento', 'Sem Reinvestimento'], 
                       color_discrete_map={'Com Reinvestimento': '#D4AF37', 'Sem Reinvestimento': '#FF4B4B'})
    st.plotly_chart(fig_comp, use_container_width=True)
    
    prejuizo = df_p['Com Reinvestimento'].iloc[-1] - df_p['Sem Reinvestimento'].iloc[-1]
    st.error(f"⚠️ Se você gastar os dividendos, deixará de ganhar R$ {prejuizo:,.2f} em {anos} anos.")
    st.success(f"💎 Reinvestindo, você terá R$ {df_p['Com Reinvestimento'].iloc[-1]:,.2f}")

# --- RESTANTE ---
elif menu == "⚙️ Gestão":
    with st.form("add"):
        t = st.text_input("Ticker").upper()
        q = st.number_input("Quantidade", min_value=0.0)
        p = st.number_input("Preço Médio", min_value=0.0)
        if st.form_submit_button("Salvar"):
            db.add_asset(t, q, p)
            st.rerun()
    if not df_db.empty: st.table(df_db[['ticker', 'qtd', 'pm']])

elif menu == "📄 PDF":
    if not df_db.empty:
        if st.button("Gerar Relatório"):
            pdf_bytes = pdf_report.generate(df_db, df_db['Patrimônio'].sum(), 0)
            st.download_button("📩 Baixar PDF", data=pdf_bytes, file_name="Report_Private.pdf")
            
