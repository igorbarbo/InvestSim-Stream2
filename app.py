import streamlit as st
import plotly.express as px
from datetime import datetime

# IMPORTANDO SEUS MÓDULOS DA PASTA SRC
from src.data_engine import fetch_data, sync_prices
from src.analytics import process_metrics
from src.ai_agent import ask_ai

# 1. CONFIGURAÇÃO DE TELA E STATUS
st.set_page_config(page_title="Terminal Igorbarbo Pro", layout="wide", page_icon="⚡")

st.markdown(f"""
    <div style="background:#11151c; padding:10px; border-radius:10px; border-left:5px solid #00ff88; margin-bottom:20px;">
        <small style="color:#888;">STATUS DO SISTEMA</small><br>
        <b>MODO:</b> Enterprise (Modular) | <b>MÉTRICA:</b> Média Ponderada pelo Patrimônio
    </div>
""", unsafe_allow_html=True)

# 2. CARREGAMENTO INICIAL
df_raw = fetch_data()

if df_raw is not None:
    # Botão de Sincronização
    if st.button("🚀 SINCRONIZAR COM A BOLSA"):
        with st.spinner("Buscando preços em tempo real..."):
            st.session_state.df_p = sync_prices(df_raw)
            st.session_state.last_sync = datetime.now().strftime("%H:%M:%S")

    # 3. INTERFACE PRINCIPAL (SÓ APARECE APÓS SINCRONIZAR)
    if "df_p" in st.session_state:
        # PROCESSA A INTELIGÊNCIA QUANTITATIVA
        df, rent_real, total = process_metrics(st.session_state.df_p)

        tab1, tab2, tab3 = st.tabs(["📊 PERFORMANCE REAL", "🧠 IA ADVISOR", "⚖️ PRIORIDADES"])

        with tab1:
            c1, c2, c3 = st.columns(3)
            c1.metric("PATRIMÔNIO TOTAL", f"R$ {total:,.2f}")
            c2.metric("RENTABILIDADE REAL (PONDERADA)", f"{rent_real:.2f}%")
            c3.metric("ÚLTIMA ATUALIZAÇÃO", st.session_state.last_sync)

            # Gráfico Profissional
            fig = px.treemap(df, path=[px.Constant("Carteira"), 'Ativo'], values='Patrimônio',
                             color='Valorização %', color_continuous_scale='RdYlGn',
                             color_continuous_midpoint=0)
            st.plotly_chart(fig, use_container_width=True)

        with tab2:
            st.subheader("💬 Consultor IA Expert")
            pergunta = st.chat_input("Ex: Qual o risco atual da minha alocação?")
            if pergunta:
                with st.spinner("IA analisando sua carteira..."):
                    resposta = ask_ai(pergunta, df)
                    st.markdown(f"> {pergunta}")
                    st.write(resposta)

        with tab3:
            st.subheader("🎯 Ranking de Aporte (Onde colocar dinheiro?)")
            st.write("O algoritmo calcula a prioridade baseada na queda do ativo e no peso dele na carteira.")
            # Mostra o ranking de quem caiu mais e tem menos peso
            st.dataframe(df[['Ativo', 'Valorização %', 'Peso', 'Prioridade']].sort_values(by='Prioridade', ascending=False), use_container_width=True)
    else:
        st.info("Clique no botão 'Sincronizar' acima para carregar os dados do mercado.")
else:
    st.error("Não foi possível carregar a planilha. Verifique a URL do Google Sheets.")
    
