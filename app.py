import streamlit as st
import plotly.express as px
from datetime import datetime
import sys
import os

# Força o Python a enxergar a pasta src
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from src.data_engine import fetch_data, sync_prices
    from src.analytics import process_metrics
    from src.ai_agent import ask_ai
except ImportError as e:
    st.error(f"Erro de Módulo: {e}")
    st.stop()

st.set_page_config(page_title="Terminal Igorbarbo V5", layout="wide", page_icon="⚡")

# CSS para visual Moderno
st.markdown("""
    <style>
        [data-testid="stMetricValue"] { font-size: 28px; color: #00ff88; }
        .stTabs [data-baseweb="tab-list"] { gap: 10px; }
        .stTabs [data-baseweb="tab"] { background-color: #11151c; border-radius: 5px; color: white; }
    </style>
""", unsafe_allow_html=True)

st.title("⚡ Terminal Igorbarbo | V5 Pro")
st.markdown("---")

df_raw = fetch_data()

if df_raw is not None:
    if "df_p" not in st.session_state:
        with st.spinner("🔄 Sincronizando Mercado..."):
            st.session_state.df_p = sync_prices(df_raw)
            st.session_state.last_sync = datetime.now().strftime("%H:%M:%S")

    if st.session_state.df_p is not None:
        df, rent_real, total = process_metrics(st.session_state.df_p)

        c1, c2, c3 = st.columns(3)
        c1.metric("PATRIMÔNIO TOTAL", f"R$ {total:,.2f}")
        c2.metric("RENTABILIDADE REAL (MWA)", f"{rent_real:.2f}%")
        c3.metric("STATUS", "CONECTADO", delta=st.session_state.last_sync)

        tab1, tab2, tab3 = st.tabs(["📊 PERFORMANCE", "🤖 IA ADVISOR V5", "🎯 RADAR"])

        with tab1:
            fig = px.treemap(df, path=['Ativo'], values='Patrimônio',
                             color='Valorização %', color_continuous_scale='RdYlGn',
                             color_continuous_midpoint=0)
            st.plotly_chart(fig, use_container_width=True)

        with tab2:
            st.subheader("💬 Inteligência Gemini 2.0")
            pergunta = st.chat_input("Ex: Por que PETR4 está caindo hoje?")
            if pergunta:
                with st.spinner("Consultando dados e Google Search..."):
                    resposta = ask_ai(pergunta, df)
                    st.markdown(f"> **Igor:** {pergunta}")
                    st.write(resposta)

        with tab3:
            st.subheader("⚖️ Prioridades de Aporte")
            st.dataframe(df[['Ativo', 'Valorização %', 'Peso', 'Prioridade']].sort_values('Prioridade', ascending=False).style.background_gradient(cmap='Greens', subset=['Prioridade']), use_container_width=True)
            
else:
    st.warning("Aguardando conexão com Google Sheets...")

if st.sidebar.button("Forçar Refresh"):
    st.session_state.clear()
    st.rerun()
    
