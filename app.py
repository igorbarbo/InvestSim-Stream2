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
            padding: 15px; border-radius: 15px; border: 1px solid #1a202c; 
        }
        [data-testid="stMetricValue"] { color: #00ff88 !important; }
        .stButton>button {
            width: 100%; border-radius: 12px; height: 3.5em;
            background-image: linear-gradient(to right, #00ff88, #00a3ff);
            color: #05070a; font-weight: bold; border: none;
        }
        #MainMenu, footer, header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 2. LOGIN ---
if 'logado' not in st.session_state: st.session_state.logado = False
SENHA_MESTRA = "igor123"

if not st.session_state.logado:
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.title("🛡️ Terminal Igorbarbo")
    senha = st.text_input("Senha Mestre:", type="password")
    if st.button("DESBLOQUEAR"):
        if senha == SENHA_MESTRA:
            st.session_state.logado = True
            st.rerun()
        else: st.error("Senha incorreta!")
    st.stop()

# --- 3. DADOS ---
@st.cache_data(ttl=600)
def carregar_dados():
    url = "https://docs.google.com/spreadsheets/d/1TWfuEvIn9YbSzEyFHKvWWD4XwppHhlj9Cm1RE6BweF8/gviz/tq?tqx=out:csv"
    try:
        df = pd.read_csv(url)
        df.columns = [c.strip() for c in df.columns]
        return df.dropna(subset=['Ativo'])
    except: return pd.DataFrame(columns=['Ativo', 'QTD', 'Preço Médio'])

if 'df_carteira' not in st.session_state: st.session_state.df_carteira = carregar_dados()

# --- 4. NAVEGAÇÃO ---
tab_dash, tab_risco, tab_val, tab_proj, tab_edit = st.tabs(["📊 DASH", "⚠️ RISCO", "⚖️ VALUATION", "🚀 PROJEÇÃO", "📂 GERENCIAR"])

with tab_dash:
    st.subheader("💎 Patrimônio Real")
    if st.button("🔄 SINCRONIZAR"):
        df = st.session_state.df_carteira.copy()
        tickers = df['Ativo'].unique().tolist()
        with st.spinner("Consultando Bolsa..."):
            dolar = float(yf.download("USDBRL=X", period="1d", progress=False)['Close'].iloc[-1])
            precos = yf.download(tickers, period="1d", progress=False)['Close']
            p_dict = {t: float(precos[t].iloc[-1] if len(tickers) > 1 else precos.iloc[-1]) for t in tickers}
            df['Preço Atual'] = df['Ativo'].map(p_dict)
            df['Patrimônio'] = df['QTD'] * df['Preço Atual'] * df['Ativo'].apply(lambda x: dolar if not x.endswith(".SA") else 1)
            st.metric("TOTAL CARTEIRA", f"R$ {df['Patrimônio'].sum():,.2f}")
            st.plotly_chart(px.pie(df, values='Patrimônio', names='Ativo', hole=0.5, template="plotly_dark"), use_container_width=True)

with tab_risco:
    st.subheader("⚠️ Concentração")
    df_risco = st.session_state.df_carteira.copy()
    if not df_risco.empty:
        st.plotly_chart(px.bar(df_risco, x='Ativo', y='QTD', template="plotly_dark").update_traces(marker_color='#00a3ff'), use_container_width=True)

with tab_val:
    st.subheader("⚖️ Valuation")
    df_val = st.session_state.df_carteira.copy()
    st.data_editor(df_val[['Ativo', 'Preço Médio']], use_container_width=True)

with tab_proj:
    st.title("🚀 Projeção Mensal Detalhada")
    
    col_input1, col_input2 = st.columns(2)
    with col_input1:
        v_aporte = st.number_input("Aporte Mensal (R$):", value=3000)
        v_anos = st.slider("Tempo (Anos):", 1, 40, 10)
    with col_input2:
        v_taxa = st.slider("Juros Anual (%):", 1.0, 20.0, 10.0)
        v_aliq = st.selectbox("Imposto sobre Lucro (%):", [15, 17.5, 20, 22.5], index=0)

    # Lógica da Bola de Neve Mês a Mês
    meses = v_anos * 12
    r_mensal = (1 + v_taxa/100)**(1/12) - 1
    
    dados_mensais = []
    saldo_anterior = 0
    total_investido = 0
    
    for mes in range(1, meses + 1):
        juros_mes = saldo_anterior * r_mensal
        total_investido += v_aporte
        saldo_atual = saldo_anterior + v_aporte + juros_mes
        dados_mensais.append({
            "Mês": mes,
            "Aporte Mensal": v_aporte,
            "Juros do Mês": juros_mes,
            "Saldo Acumulado": saldo_atual
        })
        saldo_anterior = saldo_atual

    df_proj = pd.DataFrame(dados_mensais)
    
    # Métricas Finais
    acumulado_bruto = df_proj["Saldo Acumulado"].iloc[-1]
    lucro_bruto = acumulado_bruto - total_investido
    valor_imposto = lucro_bruto * (v_aliq / 100)
    acumulado_liquido = acumulado_bruto - valor_imposto

    st.markdown("---")
    c1, c2, c3 = st.columns(3)
    c1.metric("BRUTO FINAL", f"R$ {acumulado_bruto:,.2f}")
    c2.metric("IMPOSTO", f"R$ {valor_imposto:,.2f}", delta=f"-{v_aliq}%", delta_color="inverse")
    c3.metric("LÍQUIDO", f"R$ {acumulado_liquido:,.2f}")

    # Gráfico
    st.plotly_chart(px.area(df_proj, x="Mês", y="Saldo Acumulado", title="Curva de Crescimento", template="plotly_dark").update_traces(line_color='#00ff88'), use_container_width=True)

    # TABELA DETALHADA MÊS A MÊS
    st.subheader("📋 Tabela Mensal de Rendimentos")
    st.write("Veja quanto você ganha de juros em cada mês:")
    df_visual = df_proj.copy()
    df_visual["Juros do Mês"] = df_visual["Juros do Mês"].map("R$ {:,.2f}".format)
    df_visual["Saldo Acumulado"] = df_visual["Saldo Acumulado"].map("R$ {:,.2f}".format)
    st.dataframe(df_visual, use_container_width=True)

with tab_edit:
    st.subheader("📂 Gerenciar")
    st.data_editor(st.session_state.df_carteira, use_container_width=True)
    if st.button("🚪 SAIR"):
        st.session_state.logado = False
        st.rerun()
