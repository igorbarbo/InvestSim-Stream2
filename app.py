import streamlit as st
import pandas as pd
import yfinance as yf
import gc
from Modules import db, pdf_report 
import plotly.express as px
from alpha_vantage.timeseries import TimeSeries
import time

# Configuração da Página
st.set_page_config(page_title="Igorbarbo V6 Pro", layout="wide")
db.init_db()

# Estilização Luxury
st.markdown("""
    <style>
    .stApp { background-color: #05070A; color: white; }
    [data-testid="stMetricValue"] { color: #D4AF37 !important; }
    .stProgress > div > div > div > div { background-color: #D4AF37 !important; }
    h1, h2, h3 { color: #D4AF37 !important; font-family: 'serif'; }
    </style>
    """, unsafe_allow_html=True)

# Configurações Alpha Vantage
AV_API_KEY = "DWWXZRRXKRHYCBGP"

@st.cache_data(ttl=3600)
def get_av_price(ticker):
    """Busca preço na Alpha Vantage como backup (Cache de 1h)"""
    try:
        ts = TimeSeries(key=AV_API_KEY, output_format='pandas')
        # B3 na Alpha Vantage usa .SAO
        data, _ = ts.get_quote_endpoint(symbol=f"{ticker}.SAO")
        return float(data['05. price'].iloc[0])
    except Exception:
        return 0.0

# --- NAVEGAÇÃO ---
st.sidebar.title("💎 IGORBARBO PRIVATE")
menu = st.sidebar.radio("MENU", ["🏠 Dashboard", "🎯 Projeção & Disciplina", "⚙️ Gestão", "📄 PDF"])
df_db = db.get_assets()

# --- LÓGICA DE PREÇOS (HÍBRIDA) ---
if not df_db.empty:
    try:
        # Tentativa Primária: YFinance (Rápido/Lote)
        tickers_yf = [f"{t}.SA" for t in df_db['ticker']]
        prices_data = yf.download(tickers_yf, period="1d", progress=False)['Close']
        
        if len(tickers_yf) == 1:
            df_db['Preço'] = prices_data.iloc[-1]
        else:
            last_p = prices_data.iloc[-1]
            df_db['Preço'] = df_db['ticker'].apply(lambda x: last_p.get(f"{x}.SA", 0))
            
        # Se algum preço vier zerado do YF, tenta Alpha Vantage para aquele ativo específico
        for idx, row in df_db.iterrows():
            if row['Preço'] <= 0:
                df_db.at[idx, 'Preço'] = get_av_price(row['ticker'])
                
    except Exception:
        st.sidebar.warning("YFinance Offline. Usando Alpha Vantage...")
        df_db['Preço'] = df_db['ticker'].apply(get_av_price)

    df_db['Patrimônio'] = df_db['qtd'] * df_db['Preço']

# --- DASHBOARD ---
if menu == "🏠 Dashboard":
    st.title("🏛️ Wealth Portfolio")
    if not df_db.empty:
        total = df_db['Patrimônio'].sum()
        renda = total * 0.0083 # Estimativa 10% aa
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Patrimônio Total", f"R$ {total:,.2f}")
        c2.metric("Renda Mensal Est.", f"R$ {renda:,.2f}")
        c3.metric("Próximo Aporte (Base + Renda)", f"R$ {3000 + renda:,.2f}")
        
        st.write("---")
        prog = min(total / 100000, 1.0)
        st.subheader(f"🏆 Rumo aos R$ 100k: {prog*100:.1f}%")
        st.progress(prog)
        
        fig = px.pie(df_db, values='Patrimônio', names='ticker', hole=0.6,
                     color_discrete_sequence=["#D4AF37", "#C5A028", "#B8860B", "#8B6914"])
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white")
        st.plotly_chart(fig, use_container_width=True)
    else: 
        st.info("Adicione ativos na aba Gestão para visualizar o Dashboard.")

# --- PROJEÇÃO & DISCIPLINA ---
elif menu == "🎯 Projeção & Disciplina":
    st.title("🚀 Simulador de Futuro")
    anos = st.slider("Anos de investimento", 1, 30, 10)
    taxa = 0.0083 
    aporte = 3000
    
    meses = anos * 12
    df_p = pd.DataFrame({'Mes': range(1, meses+1)})
    df_p['Com Reinvestimento'] = [aporte * (((1+taxa)**m - 1)/taxa) for m in df_p['Mes']]
    df_p['Sem Reinvestimento'] = [aporte * m for m in df_p['Mes']]
    
    st.subheader("O Custo da Indisciplina")
    fig_comp = px.line(df_p, x='Mes', y=['Com Reinvestimento', 'Sem Reinvestimento'], 
                       color_discrete_map={'Com Reinvestimento': '#D4AF37', 'Sem Reinvestimento': '#FF4B4B'})
    fig_comp.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white")
    st.plotly_chart(fig_comp, use_container_width=True)
    
    prejuizo = df_p['Com Reinvestimento'].iloc[-1] - df_p['Sem Reinvestimento'].iloc[-1]
    st.error(f"⚠️ Ao gastar os dividendos, você destrói R$ {prejuizo:,.2f} de riqueza futura.")
    st.success(f"💎 Mantendo o foco, seu patrimônio estimado é de R$ {df_p['Com Reinvestimento'].iloc[-1]:,.2f}")

# --- GESTÃO ---
elif menu == "⚙️ Gestão":
    st.title("🛠️ Gestão de Ativos")
    with st.form("add"):
        col1, col2, col3 = st.columns(3)
        t = col1.text_input("Ticker (Ex: PETR4)").upper()
        q = col2.number_input("Quantidade", min_value=0.0, step=1.0)
        p = col3.number_input("Preço Médio (R$)", min_value=0.0)
        if st.form_submit_button("💎 Adicionar à Carteira"):
            if t and q > 0:
                db.add_asset(t, q, p)
                st.success(f"{t} adicionado com sucesso!")
                time.sleep(1)
                st.rerun()

    if not df_db.empty:
        st.write("### Ativos Atuais")
        st.table(df_db[['ticker', 'qtd', 'pm']])
        if st.button("Limpar Banco de Dados"):
            # Implementar lógica de delete se necessário no seu modulo db
            pass

# --- RELATÓRIO PDF ---
elif menu == "📄 PDF":
    st.title("📑 Relatório Executivo")
    if not df_db.empty:
        if st.button("Gerar Relatório Private"):
            with st.spinner("Compilando dados..."):
                pdf_bytes = pdf_report.generate(df_db, df_db['Patrimônio'].sum(), 0)
                st.download_button("📩 Baixar Report_V6.pdf", data=pdf_bytes, file_name="Wealth_Report.pdf")
    else:
        st.warning("Sem dados para gerar relatório.")

gc.collect()
