import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import numpy as np

# --- 1. CONFIGURAÇÃO PWA E ESTILO ---
st.set_page_config(page_title="InvestSim Expert", layout="wide", page_icon="📈")

link_manifest = "https://raw.githubusercontent.com/Igorbarbo/investsim-stream2/main/manifest.json"

st.markdown(f"""
    <link rel="manifest" href="{link_manifest}">
    <style>
        .stApp {{ background-color: #05070a; color: #e0e0e0; }}
        [data-testid="stMetric"] {{ background-color: #11151c; padding: 20px; border-radius: 15px; border: 1px solid #1a202c; }}
        [data-testid="stMetricValue"] {{ color: #00ff88 !important; font-weight: bold; }}
        .stButton>button {{
            width: 100%;
            border-radius: 12px;
            background-image: linear-gradient(to right, #00ff88, #00a3ff);
            color: #05070a;
            font-weight: bold;
            height: 3em;
        }}
        /* Centralizar o Login */
        .login-box {{
            max-width: 400px;
            margin: 0 auto;
            padding: 20px;
            background-color: #11151c;
            border-radius: 15px;
            border: 1px solid #00ff88;
            text-align: center;
        }}
        #MainMenu {{visibility: hidden;}}
        footer {{visibility: hidden;}}
        header {{visibility: hidden;}}
    </style>
""", unsafe_allow_html=True)

# --- 2. SISTEMA DE SEGURANÇA (CENTRALIZADO) ---
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False

# SENHA MESTRA
SENHA_MESTRA = "igor123"

if not st.session_state.autenticado:
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image("https://cdn-icons-png.flaticon.com/512/2534/2534183.png", width=80)
        st.title("🛡️ Acesso Restrito")
        senha_input = st.text_input("Insira sua senha mestre:", type="password")
        if st.button("DESBLOQUEAR TERMINAL"):
            if senha_input == SENHA_MESTRA:
                st.session_state.autenticado = True
                st.rerun()
            else:
                st.error("Senha incorreta, Igor!")
    st.stop() # Interrompe o código aqui se não estiver logado

# --- 3. FUNÇÕES DE INTELIGÊNCIA (SÓ RODAM APÓS LOGIN) ---
@st.cache_data(ttl=600)
def carregar_dados():
    url = "https://docs.google.com/spreadsheets/d/1TWfuEvIn9YbSzEyFHKvWWD4XwppHhlj9Cm1RE6BweF8/gviz/tq?tqx=out:csv"
    try:
        df = pd.read_csv(url)
        df.columns = [c.strip() for c in df.columns]
        return df.dropna(subset=['Ativo'])
    except:
        return pd.DataFrame(columns=['Ativo', 'QTD', 'Preço Médio'])

def buscar_multiplos(tickers):
    dados = {}
    for t in tickers:
        try:
            info = yf.Ticker(t).info
            v = info.get('priceToBook' if '11' in t and not t.startswith('IVVB') else 'forwardPE', 0)
            tipo = 'P/VP' if '11' in t and not t.startswith('IVVB') else 'P/L'
            dados[t] = {'val': v, 'tipo': tipo}
        except: dados[t] = {'val': 0, 'tipo': 'N/A'}
    return dados

# --- 4. CONTEÚDO DO APP ---
if 'df_carteira' not in st.session_state:
    st.session_state.df_carteira = carregar_dados()

tab_dash, tab_radar, tab_expert, tab_risco, tab_edit = st.tabs([
    "📊 DASHBOARD", "🏆 RENDA", "🔍 VALUATION", "🛡️ RISCO", "📂 GERENCIAR"
])

with tab_dash:
    st.markdown(f"### 💎 Terminal de Patrimônio | Igorbarbo")
    if st.button("🔄 SINCRONIZAR CARTEIRA"):
        df = st.session_state.df_carteira.copy()
        tickers = df['Ativo'].unique().tolist()
        with st.spinner("Sincronizando..."):
            dolar = float(yf.download("USDBRL=X", period="1d", progress=False)['Close'].iloc[-1])
            precos = yf.download(tickers, period="1d", progress=False)['Close']
            p_dict = {t: float(precos[t].iloc[-1] if len(tickers) > 1 else precos.iloc[-1]) for t in tickers}
            df['Preço Atual'] = df['Ativo'].apply(lambda x: p_dict.get(x, 0) * (dolar if not x.endswith(".SA") else 1))
            df['Patrimônio'] = df['QTD'] * df['Preço Atual']
            
            c1, c2, c3 = st.columns(3)
            c1.metric("PATRIMÔNIO TOTAL", f"R$ {df['Patrimônio'].sum():,.2f}")
            c2.metric("META RENDA (0.8%)", f"R$ {df['Patrimônio'].sum() * 0.008:,.2f}")
            c3.metric("DÓLAR HOJE", f"R$ {dolar:,.2f}")
            
            fig = px.pie(df, values='Patrimônio', names='Ativo', hole=0.6, template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)

with tab_radar:
    st.title("🏆 Yield on Cost")
    if st.button("💰 ANALISAR DIVIDENDOS"):
        df_r = st.session_state.df_carteira.copy()
        for t in df_r['Ativo'].unique():
            divs = yf.Ticker(t).dividends
            df_r.loc[df_r['Ativo']==t, 'Div_Anual'] = divs.tail(365).sum() if not divs.empty else 0
        df_r['Renda_Mes'] = (df_r['QTD'] * df_r['Div_Anual']) / 12
        df_r['YoC'] = (df_r['Div_Anual'] / df_r['Preço Médio']) * 100
        st.metric("RENDA ESTIMADA MENSAL", f"R$ {df_r['Renda_Mes'].sum():,.2f}")
        st.dataframe(df_r[['Ativo', 'YoC', 'Renda_Mes']].style.format({'YoC': '{:.2f}%', 'Renda_Mes': 'R$ {:.2f}'}))

with tab_expert:
    st.title("🔍 Valuation")
    if st.button("🧠 RODAR ANÁLISE"):
        ind = buscar_multiplos(st.session_state.df_carteira['Ativo'].unique())
        for t, v in ind.items():
            with st.expander(f"Ativo: {t}"):
                status = "🟢 COMPRA" if (v['tipo'] == 'P/VP' and v['val'] < 0.98) or (v['tipo'] == 'P/L' and 0 < v['val'] < 12) else "🟡 NEUTRO"
                st.subheader(status)
                st.write(f"Indicador {v['tipo']}: {v['val']:.2f}")

with tab_risco:
    st.title("🛡️ Matriz de Risco")
    if st.button("🧬 GERAR CORRELAÇÃO"):
        tickers = st.session_state.df_carteira['Ativo'].unique().tolist()
        hist = yf.download(tickers, period="1y", progress=False)['Close'].pct_change().dropna()
        st.plotly_chart(px.imshow(hist.corr(), text_auto=".2f", template="plotly_dark", color_continuous_scale='RdBu_r'), use_container_width=True)

with tab_edit:
    st.title("📂 Gerenciar")
    df_edit = st.data_editor(st.session_state.df_carteira, num_rows="dynamic", use_container_width=True)
    if st.button("💾 GRAVAR DADOS"):
        st.session_state.df_carteira = df_edit
        st.success("Salvo!")

if st.sidebar.button("🚪 Sair (Logoff)"):
    st.session_state.autenticado = False
    st.rerun()
    
