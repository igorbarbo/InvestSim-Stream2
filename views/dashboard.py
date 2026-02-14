# views/dashboard.py
import streamlit as st
import pandas as pd
from datetime import datetime
from database.repository import AtivoRepository, MetaRepository
from services.preco_service import PrecoService
from services.analise_service import AnaliseService
from utils.graficos import GraficoService
from utils.exportacao import formatar_moeda

def show_dashboard(user_id):
    st.title("🏛️ Patrimônio em Tempo Real")
    
    repo = AtivoRepository()
    preco_service = PrecoService()
    analise_service = AnaliseService()
    grafico_service = GraficoService()
    meta_repo = MetaRepository()
    
    # Botão de atualizar
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        st.markdown("### 📊 Resumo da Carteira")
    with col2:
        st.caption(f"🕐 {datetime.now().strftime('%H:%M:%S')}")
    with col3:
        if st.button("🔄 Atualizar Preços"):
            st.cache_data.clear()
            st.rerun()
    
    ativos = repo.carregar_por_usuario(user_id)
    
    if not ativos:
        st.info("📭 Sua carteira está vazia. Vá em 'Gestão de Carteira' para adicionar ativos.")
        return
    
    # Buscar preços em paralelo
    tickers = [a['ticker'] for a in ativos]
    with st.spinner('🔄 Buscando preços do mercado...'):
        dados_precos = preco_service.buscar_precos_batch(tickers)
    
    # Montar DataFrame
    df = pd.DataFrame(ativos)
    precos = []
    status_list = []
    for t in tickers:
        dados = dados_precos.get(t)
        precos.append(dados.preco_atual if dados else 0)
        status_list.append(dados.status if dados else 'erro')
    
    df['preco'] = precos
    df['status'] = status_list
    df['Patrimônio'] = df['qtd'] * df['preco']
    df['Custo Total'] = df['qtd'] * df['pm']
    df['Lucro/Prejuízo'] = df['Patrimônio'] - df['Custo Total']
    df['Variação %'] = (df['preco'] / df['pm'] - 1) * 100
    
    total_patrimonio = df['Patrimônio'].sum()
    total_custo = df['Custo Total'].sum()
    total_lucro = df['Lucro/Prejuízo'].sum()
    renda_est = total_patrimonio * 0.0085  # 0.85% a.m.
    
    # Métricas
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Investido", formatar_moeda(total_custo))
    c2.metric("Patrimônio Atual", formatar_moeda(total_patrimonio))
    c3.metric("Lucro/Prejuízo", formatar_moeda(total_lucro), 
              delta=f"{((total_patrimonio/total_custo)-1)*100:.1f}%" if total_custo else "0%")
    c4.metric("Renda Mensal Est.", formatar_moeda(renda_est))
    
    st.write("---")
    
    # Tabela de ativos
    st.subheader("📋 Detalhamento por Ativo")
    df_display = df[['ticker', 'qtd', 'pm', 'preco', 'Patrimônio', 'Lucro/Prejuízo', 'Variação %', 'status']].copy()
    df_display.columns = ['Ticker', 'Qtd', 'P.Médio', 'P.Atual', 'Patrimônio', 'Lucro/Prej', 'Var %', 'Status']
    
    st.dataframe(
        df_display.style.format({
            'P.Médio': lambda x: formatar_moeda(x),
            'P.Atual': lambda x: formatar_moeda(x),
            'Patrimônio': lambda x: formatar_moeda(x),
            'Lucro/Prej': lambda x: formatar_moeda(x),
            'Var %': '{:.1f}%'
        }),
        width='stretch',
        height=400
    )
    
    # Gráficos
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        st.subheader("Distribuição por Ativo")
        fig1 = grafico_service.pizza(df['Patrimônio'], df['ticker'], "", hole=0.5)
        st.plotly_chart(fig1, use_container_width=True)
    with col_g2:
        st.subheader("Distribuição por Setor")
        setores = df.groupby('setor')['Patrimônio'].sum()
        fig2 = grafico_service.pizza(setores.values, setores.index, "", hole=0.5)
        st.plotly_chart(fig2, use_container_width=True)
    
    # Rebalanceamento (breve)
    metas = meta_repo.carregar(user_id)
    if metas:
        st.write("---")
        st.subheader("🔄 Recomendação de Rebalanceamento")
        valor_aporte = st.number_input("💰 Valor disponível para aporte (R$)", 
                                        min_value=0.0, value=0.0, step=100.0, key="aport_dash")
        # Aqui você pode chamar um serviço de rebalanceamento (simplificado)
        st.info("Para recomendações detalhadas, acesse a página 'Balanceamento'.")
