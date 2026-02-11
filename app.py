import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import numpy as np

# --- 1. CONFIGURAÇÃO E ESTILO ---
st.set_page_config(page_title="Terminal Igorbarbo", layout="wide", page_icon="📈")

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

# --- 3. CARREGAMENTO DE DADOS ---
@st.cache_data(ttl=600)
def carregar_dados():
    url = "https://docs.google.com/spreadsheets/d/1TWfuEvIn9YbSzEyFHKvWWD4XwppHhlj9Cm1RE6BweF8/gviz/tq?tqx=out:csv"
    try:
        df = pd.read_csv(url)
        df.columns = [c.strip() for c in df.columns]
        return df.dropna(subset=['Ativo'])
    except: return pd.DataFrame(columns=['Ativo', 'QTD', 'Preço Médio'])

if 'df_carteira' not in st.session_state: st.session_state.df_carteira = carregar_dados()

# --- 4. ABAS ---
tab_dash, tab_risco, tab_proj, tab_edit = st.tabs(["📊 DASHBOARD", "⚠️ RISCO", "🚀 BOLA DE NEVE", "📂 GERENCIAR"])

with tab_dash:
    st.subheader("💎 Patrimônio Real")
    if st.button("🔄 SINCRONIZAR"):
        df = st.session_state.df_carteira.copy()
        tickers = df['Ativo'].unique().tolist()
        with st.spinner("Consultando Mercado..."):
            dolar = float(yf.download("USDBRL=X", period="1d", progress=False)['Close'].iloc[-1])
            precos = yf.download(tickers, period="1d", progress=False)['Close']
            p_dict = {t: float(precos[t].iloc[-1] if len(tickers) > 1 else precos.iloc[-1]) for t in tickers}
            df['Patrimônio'] = df['QTD'] * df['Ativo'].apply(lambda x: p_dict.get(x, 0) * (dolar if not x.endswith(".SA") else 1))
            st.metric("TOTAL ATUAL", f"R$ {df['Patrimônio'].sum():,.2f}")
            st.plotly_chart(px.pie(df, values='Patrimônio', names='Ativo', hole=0.5, template="plotly_dark"), use_container_width=True)

with tab_risco:
    st.subheader("⚠️ Concentração")
    df_risco = st.session_state.df_carteira.copy()
    if not df_risco.empty:
        st.plotly_chart(px.bar(df_risco, x='Ativo', y='QTD', template="plotly_dark").update_traces(marker_color='#00a3ff'), use_container_width=True)

with tab_proj:
    st.title("🚀 Simulador Bola de Neve")
    st.write("Veja como o seu investimento cresce e quanto ele te rende mensalmente.")
    
    col1, col2 = st.columns(2)
    with col1:
        v_aporte = st.number_input("Quanto você vai investir por mês (R$):", value=3000, step=100)
        v_anos = st.slider("Por quantos anos?", 1, 40, 10)
    with col2:
        v_taxa = st.slider("Taxa de Juros Anual Esperada (%):", 1.0, 20.0, 10.0)
        v_imposto = st.selectbox("Imposto de Renda sobre o lucro (%):", [15, 17.5, 20, 22.5], index=0)

    # Lógica Matemática da Projeção
    meses = v_anos * 12
    r_mensal = (1 + v_taxa/100)**(1/12) - 1
    
    dados_mensais = []
    patrimonio_acumulado = 0
    total_investido_do_bolso = 0
    
    for mes in range(1, meses + 1):
        juros_ganho_no_mes = patrimonio_acumulado * r_mensal
        total_investido_do_bolso += v_aporte
        patrimonio_acumulado = patrimonio_acumulado + v_aporte + juros_ganho_no_mes
        
        dados_mensais.append({
            "Mês": mes,
            "Total Investido (Bolso)": total_investido_do_bolso,
            "Rendimento do Mês (Juros)": juros_ganho_no_mes,
            "Patrimônio Total (Bolo)": patrimonio_acumulado
        })

    df_proj = pd.DataFrame(dados_mensais)
    
    # Cálculos de Imposto
    lucro_bruto = patrimonio_acumulado - total_investido_do_bolso
    valor_ir = lucro_bruto * (v_imposto / 100)
    patrimonio_liquido = patrimonio_acumulado - valor_ir

    st.markdown("---")
    
    # Métricas de Resumo
    m1, m2, m3 = st.columns(3)
    m1.metric("PATRIMÔNIO BRUTO", f"R$ {patrimonio_acumulado:,.2f}")
    m2.metric("LUCRO EM JUROS", f"R$ {lucro_bruto:,.2f}")
    m3.metric("LÍQUIDO (PÓS IR)", f"R$ {patrimonio_liquido:,.2f}")

    # Gráfico de Evolução
    fig_evolucao = px.area(df_proj, x="Mês", y="Patrimônio Total (Bolo)", 
                           title="A Escada da Liberdade Financeira", template="plotly_dark")
    fig_evolucao.update_traces(line_color='#00ff88', fillcolor='rgba(0, 255, 136, 0.2)')
    st.plotly_chart(fig_evolucao, use_container_width=True)

    # TABELA DETALHADA MÊS A MÊS
    st.subheader("📋 Tabela Mensal: O Crescimento da Bola de Neve")
    st.write("Acompanhe o rendimento subindo mês a mês:")
    
    # Formatação para exibição
    df_visual = df_proj.copy()
    for col in ["Total Investido (Bolso)", "Rendimento do Mês (Juros)", "Patrimônio Total (Bolo)"]:
        df_visual[col] = df_visual[col].map("R$ {:,.2f}".format)
    
    st.dataframe(df_visual, use_container_width=True)

with tab_edit:
    st.subheader("📂 Gerenciar Dados")
    st.data_editor(st.session_state.df_carteira, use_container_width=True)
    if st.button("🚪 SAIR"):
        st.session_state.logado = False
        st.rerun()
        
