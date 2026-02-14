# views/analise_avancada.py
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from database.repository import AtivoRepository
from services.preco_service import PrecoService
from services.analise_service import AnaliseService
from utils.exportacao import exportar_para_excel, exportar_para_csv
from utils.graficos import GraficoService

def show_analise_avancada(user_id):
    st.title("📊 Análise Avançada da Carteira")
    
    repo = AtivoRepository()
    preco_service = PrecoService()
    analise_service = AnaliseService()
    grafico_service = GraficoService()
    
    ativos = repo.carregar_por_usuario(user_id)
    if not ativos:
        st.info("Adicione ativos para análises.")
        return
    
    with st.spinner("Atualizando dados..."):
        dados_precos = preco_service.buscar_precos_batch([a['ticker'] for a in ativos])
    
    df = pd.DataFrame(ativos)
    df['preco'] = [dados_precos[t].preco_atual for t in df['ticker']]
    df['Patrimônio'] = df['qtd'] * df['preco']
    
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Correlação", "📈 Risco", "💰 Análise Preço", "📥 Exportar"])
    
    with tab1:
        st.subheader("Matriz de Correlação")
        from services.preco_service import PrecoService
        ps = PrecoService()
        dados = {}
        for t in df['ticker']:
            dados_hist = ps._buscar_dados_single(t)
            if dados_hist.status == "ok":
                dados[t] = dados_hist.historico['Adj Close']
        if len(dados) >= 2:
            df_corr = pd.DataFrame(dados).pct_change().corr()
            fig = px.imshow(df_corr, text_auto=True, aspect="auto", color_continuous_scale='RdYlGn')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Precisa de pelo menos 2 ativos com histórico.")
    
    with tab2:
        st.subheader("Análise de Risco")
        from services.analise_service import AnaliseService
        asrv = AnaliseService()
        riscos = {}
        for t in df['ticker']:
            d = dados_precos[t]
            if d.status == "ok":
                ret = d.historico['Adj Close'].pct_change().dropna()
                riscos[t] = {
                    'Retorno Anual': ret.mean() * 252 * 100,
                    'Volatilidade': ret.std() * (252**0.5) * 100,
                    'Drawdown Máx': (d.historico['Adj Close'] / d.historico['Adj Close'].cummax() - 1).min() * 100
                }
        if riscos:
            df_risco = pd.DataFrame(riscos).T
            df_risco.columns = ['Retorno Anual %', 'Volatilidade %', 'Drawdown Máx %']
            st.dataframe(df_risco.style.format("{:.2f}%"), width='stretch')
            fig = px.scatter(df_risco, x='Volatilidade %', y='Retorno Anual %', text=df_risco.index,
                             title="Risco x Retorno")
            fig.update_traces(textposition='top center')
            st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        st.subheader("Análise de Preço - Caro ou Barato?")
        ticker = st.selectbox("Selecione um ativo", df['ticker'].tolist())
        if ticker:
            dados = dados_precos[ticker]
            if dados.status == "ok":
                resultado = analise_service.analisar(dados)
                st.markdown(f"<h3 style='color:{resultado.cor}'>{resultado.mensagem}</h3>", unsafe_allow_html=True)
                st.markdown(resultado.explicacao)
                fig = grafico_service.historico_precos(dados, ticker)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
    
    with tab4:
        st.subheader("Exportar Dados")
        df_export = df[['ticker', 'qtd', 'pm', 'preco', 'Patrimônio']].copy()
        df_export['Lucro/Prejuízo'] = df_export['Patrimônio'] - df_export['qtd'] * df_export['pm']
        excel = exportar_para_excel(df_export)
        csv = exportar_para_csv(df_export)
        col1, col2 = st.columns(2)
        with col1:
            st.download_button("📥 Excel", data=excel, file_name=f"carteira_{datetime.now().strftime('%Y%m%d')}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        with col2:
            st.download_button("📥 CSV", data=csv, file_name=f"carteira_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv")
