import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import numpy as np

# --- 1. CONFIGURAÇÃO PWA E ESTILO DE ALTA FIDELIDADE ---
st.set_page_config(page_title="InvestSim Expert", layout="wide", page_icon="📈")

# Link RAW para o seu manifesto PWA
link_manifest = "https://raw.githubusercontent.com/Igorbarbo/investsim-stream2/main/manifest.json"

st.markdown(f"""
    <link rel="manifest" href="{link_manifest}">
    <style>
        /* Estilo Deep Dark */
        .stApp {{ background-color: #05070a; color: #e0e0e0; }}
        
        /* Cards de Métricas */
        [data-testid="stMetric"] {{
            background-color: #11151c;
            padding: 20px;
            border-radius: 15px;
            border: 1px solid #1a202c;
            box-shadow: 0px 4px 10px rgba(0,0,0,0.3);
        }}
        [data-testid="stMetricValue"] {{ color: #00ff88 !important; font-weight: bold; font-family: 'Courier New'; }}
        
        /* Botões com Gradiente */
        .stButton>button {{
            width: 100%;
            border-radius: 12px;
            background-image: linear-gradient(to right, #00ff88, #00a3ff);
            color: #05070a;
            font-weight: bold;
            border: none;
            height: 3em;
            transition: 0.3s;
        }}
        .stButton>button:hover {{
            transform: scale(1.02);
            box-shadow: 0px 0px 15px rgba(0, 255, 136, 0.4);
        }}

        /* Esconder Elementos Streamlit para cara de App */
        #MainMenu {{visibility: hidden;}}
        footer {{visibility: hidden;}}
        header {{visibility: hidden;}}
    </style>
""", unsafe_allow_html=True)

# --- 2. SISTEMA DE SEGURANÇA (LOGIN) ---
# A senha fica na barra lateral para não poluir o visual principal
st.sidebar.title("🔐 Área Segura")
senha_digitada = st.sidebar.text_input("Senha de Acesso:", type="password")

# --- ALTERE SUA SENHA AQUI ---
SENHA_MESTRA = "igor123"

# --- 3. FUNÇÕES DE INTELIGÊNCIA ---
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
            # Lógica P/VP para FIIs e P/L para Ações
            if '11' in t and not t.startswith('IVVB'):
                v = info.get('priceToBook', 0)
                dados[t] = {'val': v, 'tipo': 'P/VP'}
            else:
                v = info.get('forwardPE', info.get('trailingPE', 0))
                dados[t] = {'val': v, 'tipo': 'P/L'}
        except:
            dados[t] = {'val': 0, 'tipo': 'N/A'}
    return dados

# --- 4. LÓGICA DE EXIBIÇÃO ---
if senha_digitada == SENHA_MESTRA:
    st.sidebar.success("Identidade Confirmada!")
    
    # Inicializa os dados na sessão
    if 'df_carteira' not in st.session_state:
        st.session_state.df_carteira = carregar_dados()

    # Criação das Abas
    tab_dash, tab_radar, tab_expert, tab_risco, tab_edit = st.tabs([
        "📊 DASHBOARD", "🏆 RENDA", "🔍 VALUATION", "🛡️ RISCO", "📂 GERENCIAR"
    ])

    # --- ABA 1: DASHBOARD ---
    with tab_dash:
        st.markdown(f"### 💎 Terminal de Patrimônio | Igorbarbo")
        if st.button("🔄 SINCRONIZAR CARTEIRA"):
            df = st.session_state.df_carteira.copy()
            tickers = df['Ativo'].unique().tolist()
            with st.spinner("Consultando Bolsa de Valores..."):
                dolar = float(yf.download("USDBRL=X", period="1d", progress=False)['Close'].iloc[-1])
                precos = yf.download(tickers, period="1d", progress=False)['Close']
                p_dict = {t: float(precos[t].iloc[-1] if len(tickers) > 1 else precos.iloc[-1]) for t in tickers}
                df['Preço Atual'] = df['Ativo'].apply(lambda x: p_dict.get(x, 0) * (dolar if not x.endswith(".SA") else 1))
                df['Patrimônio'] = df['QTD'] * df['Preço Atual']
                
                c1, c2, c3 = st.columns(3)
                total_geral = df['Patrimônio'].sum()
                c1.metric("PATRIMÔNIO TOTAL", f"R$ {total_geral:,.2f}")
                c2.metric("META RENDA (0.8%)", f"R$ {total_geral * 0.008:,.2f}")
                c3.metric("DÓLAR HOJE", f"R$ {dolar:,.2f}")
                
                fig = px.pie(df, values='Patrimônio', names='Ativo', hole=0.6)
                fig.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig, use_container_width=True)

    # --- ABA 2: RENDA (YIELD ON COST) ---
    with tab_radar:
        st.title("🏆 Yield on Cost & Dividendos")
        if st.button("💰 CALCULAR RENDIMENTOS"):
            df_r = st.session_state.df_carteira.copy()
            for t in df_r['Ativo'].unique():
                divs = yf.Ticker(t).dividends
                df_r.loc[df_r['Ativo']==t, 'Div_Anual'] = divs.tail(365).sum() if not divs.empty else 0
            df_r['Renda_Mes'] = (df_r['QTD'] * df_r['Div_Anual']) / 12
            df_r['YoC'] = (df_r['Div_Anual'] / df_r['Preço Médio']) * 100
            st.metric("RENDA MÉDIA MENSAL", f"R$ {df_r['Renda_Mes'].sum():,.2f}")
            st.dataframe(df_r[['Ativo', 'YoC', 'Renda_Mes']].style.format({'YoC': '{:.2f}%', 'Renda_Mes': 'R$ {:.2f}'}), use_container_width=True)

    # --- ABA 3: VALUATION ---
    with tab_expert:
        st.title("🔍 Inteligência de Valuation")
        if st.button("🧠 RODAR ANÁLISE DE MERCADO"):
            indicadores = buscar_multiplos(st.session_state.df_carteira['Ativo'].unique())
            for t, info in indicadores.items():
                val, tipo = info['val'], info['tipo']
                with st.expander(f"Análise: {t}"):
                    if tipo == "P/VP":
                        status = "🟢 COMPRA" if val < 0.98 else "🔴 CARO" if val > 1.05 else "🟡 JUSTO"
                    else:
                        status = "🟢 COMPRA" if 0 < val < 12 else "🔴 CARO" if val > 20 else "🟡 JUSTO"
                    st.subheader(status)
                    st.write(f"Indicador {tipo}: {val:.2f}")

    # --- ABA 4: RISCO (MATRIZ) ---
    with tab_risco:
        st.title("🛡️ Matriz de Correlação")
        if st.button("🧬 ANALISAR PROTEÇÃO"):
            tickers = st.session_state.df_carteira['Ativo'].unique().tolist()
            hist = yf.download(tickers, period="1y", progress=False)['Close'].pct_change().dropna()
            fig_corr = px.imshow(hist.corr(), text_auto=".2f", color_continuous_scale='RdBu_r', template="plotly_dark")
            st.plotly_chart(fig_corr, use_container_width=True)

    # --- ABA 5: GERENCIAR ---
    with tab_edit:
        st.title("📂 Central de Dados")
        df_edit = st.data_editor(st.session_state.df_carteira, num_rows="dynamic", use_container_width=True)
        if st.button("💾 GRAVAR ALTERAÇÕES NA PLANILHA"):
            st.session_state.df_carteira = df_edit
            st.success("Dados atualizados com sucesso!")

else:
    # Tela de bloqueio quando a senha não foi digitada ou está errada
    if senha_digitada != "":
        st.sidebar.error("Acesso Negado!")
    
    st.title("🛡️ Sistema de Investimentos Igorbarbo")
    st.warning("Aguardando autenticação para carregar dados patrimoniais.")
    st.info("Digite a senha secreta na barra lateral ⬅️ para desbloquear o terminal.")
    
    # Ícone central de proteção
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.image("https://cdn-icons-png.flaticon.com/512/2534/2534183.png", width=150)
