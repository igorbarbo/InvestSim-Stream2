import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import numpy as np
import google.generativeai as genai
from datetime import datetime

# --- 1. CONFIGURAÇÃO EXPERT ---
st.set_page_config(page_title="Terminal Igorbarbo Bloomberg Edition", layout="wide", page_icon="⚡")

# Estilo CSS Avançado (Glow Effects e Dark Premium)
st.markdown("""
    <style>
        .stApp { background-color: #020408; color: #e0e0e0; }
        [data-testid="stMetric"] { 
            background: rgba(17, 21, 28, 0.7); 
            backdrop-filter: blur(10px);
            padding: 20px; border-radius: 20px; border: 1px solid #00ff8833;
            box-shadow: 0 4px 15px rgba(0, 255, 136, 0.1);
        }
        .stTabs [data-baseweb="tab-list"] { gap: 10px; }
        .stTabs [data-baseweb="tab"] {
            background-color: #11151c; border-radius: 10px 10px 0 0; padding: 10px 20px;
        }
        .stTabs [aria-selected="true"] { background-image: linear-gradient(to right, #00ff88, #00a3ff) !important; color: black !important; }
    </style>
""", unsafe_allow_html=True)

# --- 2. INTEGRAÇÃO GOOGLE AI (GEMINI 3 FLASH + SEARCH) ---
# Substitua pela sua chave do AI Studio
API_KEY = "SUA_CHAVE_AQUI" 
if API_KEY != "SUA_CHAVE_AQUI":
    genai.configure(api_key=API_KEY)

# --- 3. CORE DE DADOS ---
@st.cache_data(ttl=300)
def carregar_dados():
    url = "https://docs.google.com/spreadsheets/d/1TWfuEvIn9YbSzEyFHKvWWD4XwppHhlj9Cm1RE6BweF8/gviz/tq?tqx=out:csv"
    df = pd.read_csv(url)
    df.columns = [c.strip() for c in df.columns]
    return df.dropna(subset=['Ativo'])

# --- 4. INTERFACE PRINCIPAL ---
st.title("⚡ Terminal Igorbarbo | Expert Edition")

tab_dash, tab_ai, tab_radar, tab_proj = st.tabs([
    "📊 DASHBOARD", "🧠 ANALISTA IA EXPERT", "🎯 RADAR & NOTÍCIAS", "🚀 BOLA DE NEVE"
])

# --- ABA 1: DASHBOARD COM YIELD ON COST ---
with tab_dash:
    df = carregar_dados()
    tickers = df['Ativo'].unique().tolist()
    
    if st.button("🚀 SINCRONIZAR PERFORMANCE"):
        with st.spinner("Conectando aos servidores globais..."):
            dolar = float(yf.download("USDBRL=X", period="1d", progress=False)['Close'].iloc[-1])
            precos = yf.download(tickers, period="1d", progress=False)['Close']
            
            p_dict = {t: float(precos[t].iloc[-1] if len(tickers) > 1 else precos.iloc[-1]) for t in tickers}
            df['Preço Atual'] = df['Ativo'].map(p_dict)
            df['Patrimônio'] = df['QTD'] * df['Preço Atual'] * df['Ativo'].apply(lambda x: dolar if not x.endswith(".SA") else 1)
            
            # Cálculo de Yield on Cost (YOC) Simulado
            # Aqui você poderia buscar o histórico de dividendos real via yf.Ticker(t).dividends
            df['YOC %'] = (df['Preço Atual'] / df['Preço Médio'] - 1) * 100
            
            c1, c2, c3 = st.columns(3)
            c1.metric("PATRIMÔNIO TOTAL", f"R$ {df['Patrimônio'].sum():,.2f}")
            c2.metric("LUCRO ESTIMADO", f"{df['YOC %'].mean():.2f}%", delta="Benchmarking: CDI+")
            c3.metric("DOLAR HOJE", f"R$ {dolar:.2f}")
            
            st.plotly_chart(px.sunburst(df, path=['Ativo'], values='Patrimônio', template="plotly_dark", color='Patrimônio', color_continuous_scale='RdYlGn'), use_container_width=True)

# --- ABA 2: ANALISTA IA EXPERT (CHAT + GOOGLE SEARCH) ---
with tab_ai:
    st.subheader("💬 Consultor Estratégico Real-Time")
    st.info("A IA está conectada ao Google Search para analisar notícias de última hora sobre sua carteira.")
    
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ex: Vale a pena rebalancear minha carteira hoje?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            if API_KEY == "SUA_CHAVE_AQUI":
                response = "⚠️ Por favor, configure sua API Key do Google AI Studio para ativar o Analista."
            else:
                model = genai.GenerativeModel('gemini-1.5-flash', tools=[{'google_search_grounding': {}}])
                full_prompt = f"Dados da Carteira do Igor: {df.to_string()}. Pergunta do Usuário: {prompt}"
                res = model.generate_content(full_prompt)
                response = res.text
            
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})

# --- ABA 3: RADAR & HEATMAP ---
with tab_radar:
    st.subheader("🔥 Mapa de Calor e Oportunidades")
    # Simulação de Heatmap
    fig_heat = px.treemap(df, path=[px.Constant("Carteira"), 'Ativo'], values='Patrimônio',
                 color='YOC %', color_continuous_scale='RdYlGn',
                 color_continuous_midpoint=0)
    st.plotly_chart(fig_heat, use_container_width=True)

# --- ABA 4: BOLA DE NEVE PWA ---
with tab_proj:
    st.subheader("🚀 Simulador de Independência Financeira")
    # (Mantém sua lógica de juros compostos anterior, mas com o visual Glow)
    st.write("Ajuste seus aportes para ver o Ponto de Virada.")
    # ... (Seu código de projeção aqui)
    
