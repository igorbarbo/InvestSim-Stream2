import streamlit as st
import pandas as pd
import yfinance as yf
import gc
import time
from Modules import db, pdf_report 
import plotly.express as px
from alpha_vantage.timeseries import TimeSeries

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
    .stDataFrame { background-color: #0F1116; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# Chave Alpha Vantage
AV_API_KEY = "DWWXZRRXKRHYCBGP"

@st.cache_data(ttl=3600)
def get_av_price(ticker):
    try:
        ts = TimeSeries(key=AV_API_KEY, output_format='pandas')
        data, _ = ts.get_quote_endpoint(symbol=f"{ticker}.SAO")
        return float(data['05. price'].iloc[0])
    except:
        return 0.0

# --- NAVEGAÇÃO ---
st.sidebar.title("💎 IGORBARBO PRIVATE")
menu = st.sidebar.radio("MENU", ["🏠 Dashboard", "🎯 Projeção & Disciplina", "💡 Sugestão de Aporte", "⚙️ Gestão", "📄 PDF"])
df_db = db.get_assets()

# --- ATUALIZAÇÃO DE PREÇOS ---
if not df_db.empty:
    try:
        tickers_yf = [f"{t}.SA" for t in df_db['ticker']]
        prices = yf.download(tickers_yf, period="1d", progress=False)['Close']
        if len(tickers_yf) == 1:
            df_db['Preço'] = prices.iloc[-1]
        else:
            last_p = prices.iloc[-1]
            df_db['Preço'] = df_db['ticker'].apply(lambda x: last_p.get(f"{x}.SA", 0))
    except:
        st.sidebar.warning("Usando Alpha Vantage...")
        df_db['Preço'] = df_db['ticker'].apply(get_av_price)
    
    df_db['Patrimônio'] = df_db['qtd'] * df_db['Preço']

# --- LÓGICA DE TELAS ---
if menu == "🏠 Dashboard":
    st.title("🏛️ Wealth Portfolio")
    if not df_db.empty:
        total = df_db['Patrimônio'].sum()
        renda_estimada = total * 0.0085 # Média de 0.85% am
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Patrimônio Total", f"R$ {total:,.2f}")
        c2.metric("Renda Passiva Est.", f"R$ {renda_estimada:,.2f}")
        c3.metric("Poder de Aporte", f"R$ {3000 + renda_estimada:,.2f}")
        
        st.write("---")
        prog = min(total / 100000, 1.0)
        st.subheader(f"🏆 Meta R$ 100k: {prog*100:.1f}%")
        st.progress(prog)
        
        fig = px.pie(df_db, values='Patrimônio', names='ticker', hole=0.6,
                     color_discrete_sequence=["#D4AF37", "#C5A028", "#8B6914"])
        st.plotly_chart(fig, use_container_width=True)

elif menu == "💡 Sugestão de Aporte":
    st.title("🎯 Estratégia de Alocação")
    valor = st.number_input("Valor para investir hoje (R$)", min_value=0.0, value=150.0)
    
    # Base de dados de ativos reais para sua meta de 0.75% - 1%
    sugestoes = [
        {"Ativo": "MXRF11", "Tipo": "FII Papel", "Preço": 10.50, "Yield": 1.0},
        {"Ativo": "GALG11", "Tipo": "FII Logística", "Preço": 9.20, "Yield": 0.9},
        {"Ativo": "CDB 110%", "Tipo": "Renda Fixa", "Preço": 100.00, "Yield": 0.85},
        {"Ativo": "VISC11", "Tipo": "FII Shopping", "Preço": 120.00, "Yield": 0.78}
    ]
    
    df_s = pd.DataFrame(sugestoes)
    df_s['Cotas'] = (valor // df_s['Preço']).astype(int)
    df_s['Renda Mensal (R$)'] = (df_s['Cotas'] * df_s['Preço'] * (df_s['Yield']/100))
    
    st.write(f"### Onde colocar seus R$ {valor:.2f}:")
    st.table(df_s.style.format({'Preço': 'R$ {:.2f}', 'Yield': '{:.2f}%', 'Renda Mensal (R$)': 'R$ {:.2f}'}))
    
    st.info("💡 Ativos de 'Base 10' (como MXRF11) permitem que você compre mais cotas com pouco dinheiro, acelerando os juros compostos.")

elif menu == "🎯 Projeção & Disciplina":
    st.title("🚀 Simulador de Futuro")
    anos = st.slider("Anos", 1, 30, 10)
    aporte = st.number_input("Aporte Mensal", value=150)
    taxa = 0.0085 # 0.85% am
    
    meses = anos * 12
    df_p = pd.DataFrame({'Mes': range(1, meses+1)})
    df_p['Com Reinvestimento'] = [aporte * (((1+taxa)**m - 1)/taxa) for m in df_p['Mes']]
    df_p['Sem Reinvestimento'] = [aporte * m for m in df_p['Mes']]
    
    st.plotly_chart(px.line(df_p, x='Mes', y=['Com Reinvestimento', 'Sem Reinvestimento'], 
                           color_discrete_map={'Com Reinvestimento': '#D4AF37', 'Sem Reinvestimento': '#FF4B4B'}))

elif menu == "⚙️ Gestão":
    st.title("⚙️ Gerenciar Carteira")
    with st.form("add_asset"):
        t = st.text_input("Ticker (Ex: PETR4)").upper()
        q = st.number_input("Quantidade", min_value=0.0)
        p = st.number_input("Preço Médio", min_value=0.0)
        if st.form_submit_button("Salvar"):
            db.add_asset(t, q, p)
            st.rerun()
    st.dataframe(df_db[['ticker', 'qtd', 'pm']])

elif menu == "📄 PDF":
    st.title("📑 Relatório")
    if not df_db.empty and st.button("Gerar PDF"):
        pdf_bytes = pdf_report.generate(df_db, df_db['Patrimônio'].sum(), 0)
        st.download_button("Baixar Relatório", pdf_bytes, "Invest_Report.pdf")

gc.collect()
