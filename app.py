import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import numpy as np

# --- 1. CONFIGURAÇÃO E ESTILO ---
st.set_page_config(page_title="InvestSim Expert", layout="wide", page_icon="📈")

st.markdown("""
    <style>
        .stApp { background-color: #05070a; color: #e0e0e0; }
        [data-testid="stMetric"] { 
            background-color: #11151c; 
            padding: 15px; 
            border-radius: 15px; 
            border: 1px solid #1a202c; 
        }
        [data-testid="stMetricValue"] { color: #00ff88 !important; }
        .stButton>button {
            width: 100%; border-radius: 12px; height: 3.5em;
            background-image: linear-gradient(to right, #00ff88, #00a3ff);
            color: #05070a; font-weight: bold; border: none;
        }
        #MainMenu, footer, header {visibility: hidden;}
        .stTabs [data-baseweb="tab-list"] { gap: 10px; }
        .stTabs [data-baseweb="tab"] {
            background-color: #11151c;
            border-radius: 10px 10px 0px 0px;
            padding: 10px;
            color: white;
        }
    </style>
""", unsafe_allow_html=True)

# --- 2. SISTEMA DE LOGIN ---
if 'logado' not in st.session_state: 
    st.session_state.logado = False

# SUA SENHA MESTRA
SENHA_MESTRA = "igor123"

if not st.session_state.logado:
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image("https://cdn-icons-png.flaticon.com/512/2534/2534183.png", width=80)
        st.title("🛡️ Terminal Igorbarbo")
        senha_input = st.text_input("Senha Mestre:", type="password")
        if st.button("DESBLOQUEAR TERMINAL"):
            if senha_input == SENHA_MESTRA:
                st.session_state.logado = True
                st.rerun()
            else:
                st.error("Senha incorreta!")
    st.stop()

# --- 3. CARREGAMENTO DE DADOS ---
@st.cache_data(ttl=600)
def carregar_dados():
    # Sua URL do Google Sheets (CSV)
    url = "https://docs.google.com/spreadsheets/d/1TWfuEvIn9YbSzEyFHKvWWD4XwppHhlj9Cm1RE6BweF8/gviz/tq?tqx=out:csv"
    try:
        df = pd.read_csv(url)
        df.columns = [c.strip() for c in df.columns]
        return df.dropna(subset=['Ativo'])
    except:
        return pd.DataFrame(columns=['Ativo', 'QTD', 'Preço Médio'])

if 'df_carteira' not in st.session_state:
    st.session_state.df_carteira = carregar_dados()

# --- 4. NAVEGAÇÃO POR ABAS ---
tab_dash, tab_proj, tab_edit = st.tabs(["📊 DASHBOARD", "🚀 PROJEÇÃO DE FUTURO", "📂 GERENCIAR"])

# --- ABA 1: DASHBOARD ---
with tab_dash:
    st.markdown("### 💎 Patrimônio Real")
    if st.button("🔄 SINCRONIZAR CARTEIRA"):
        df = st.session_state.df_carteira.copy()
        tickers = df['Ativo'].unique().tolist()
        with st.spinner("Consultando Mercado Financeiro..."):
            dolar = float(yf.download("USDBRL=X", period="1d", progress=False)['Close'].iloc[-1])
            precos = yf.download(tickers, period="1d", progress=False)['Close']
            
            # Lógica para preço unitário ou múltiplos ativos
            p_dict = {t: float(precos[t].iloc[-1] if len(tickers) > 1 else precos.iloc[-1]) for t in tickers}
            
            # Calcula valor total (com conversão de dólar para ativos fora da B3)
            df['Patrimônio'] = df['QTD'] * df['Ativo'].apply(lambda x: p_dict.get(x, 0) * (dolar if not x.endswith(".SA") else 1))
            
            total_geral = df['Patrimônio'].sum()
            c1, c2 = st.columns(2)
            c1.metric("TOTAL ACUMULADO", f"R$ {total_geral:,.2f}")
            c2.metric("DÓLAR HOJE", f"R$ {dolar:,.2f}")
            
            fig = px.pie(df, values='Patrimônio', names='Ativo', hole=0.5, template="plotly_dark")
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)

# --- ABA 2: PROJEÇÃO (SIMULADOR) ---
with tab_proj:
    st.title("🚀 Planejamento de Futuro")
    st.write("Simule quanto você terá e quanto vai ganhar de juros por mês.")
    
    col1, col2 = st.columns(2)
    with col1:
        v_aporte = st.number_input("Aporte Mensal (R$):", min_value=0, value=3000, step=100)
        v_anos = st.slider("Tempo de Investimento (Anos):", 1, 40, 10)
    with col2:
        v_taxa = st.slider("Taxa de Juros Anual (%):", 1.0, 20.0, 10.0)
        v_yield = st.slider("Rendimento de Dividendos Mensal (%):", 0.1, 2.0, 0.8)

    # Cálculos
    meses = v_anos * 12
    taxa_mensal = (1 + v_taxa/100)**(1/12) - 1
    
    if taxa_mensal > 0:
        patrimonio_final = v_aporte * (((1 + taxa_mensal)**meses - 1) / taxa_mensal)
    else:
        patrimonio_final = v_aporte * meses
        
    total_do_bolso = v_aporte * meses
    total_so_juros = patrimonio_final - total_do_bolso
    renda_mensal_estimada = patrimonio_final * (v_yield / 100)

    st.markdown("---")
    m1, m2, m3 = st.columns(3)
    m1.metric("VALOR AO FINAL", f"R$ {patrimonio_final:,.2f}")
    m2.metric("TOTAL EM JUROS", f"R$ {total_so_juros:,.2f}")
    m3.metric("RENDA MENSAL", f"R$ {renda_mensal_estimada:,.2f}")

    st.success(f"🎯 Ao final de {v_anos} anos, seu patrimônio renderia **R$ {renda_mensal_estimada:,.2f} por mês**.")

    # Gráfico de Projeção
    eixo_x = list(range(1, meses + 1))
    eixo_y = [v_aporte * (((1 + taxa_mensal)**i - 1) / taxa_mensal) if taxa_mensal > 0 else v_aporte * i for i in eixo_x]
    
    fig_evolucao = px.area(x=eixo_x, y=eixo_y, title="A Curva do seu Enriquecimento",
                           labels={'x': 'Meses', 'y': 'Patrimônio (R$)'}, template="plotly_dark")
    fig_evolucao.update_traces(line_color='#00ff88', fillcolor='rgba(0, 255, 136, 0.2)')
    st.plotly_chart(fig_evolucao, use_container_width=True)

# --- ABA 3: GERENCIAR ---
with tab_edit:
    st.subheader("📂 Gerenciamento de Dados")
    st.write("Os dados abaixo são sincronizados com sua planilha do Google.")
    
    # Editor de dados para ajustes rápidos
    df_editado = st.data_editor(st.session_state.df_carteira, num_rows="dynamic", use_container_width=True)
    
    st.markdown("---")
    if st.button("🚪 LOGOFF (SAIR DO TERMINAL)"):
        st.session_state.logado = False
        st.rerun()
        
