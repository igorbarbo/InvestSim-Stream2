import streamlit as st

def show_dashboard(user_id):
    st.title("🏠 Private Dashboard")
    
    # Lazy Loading do repository
    from database.repository import DatabaseManager
    
    # Recupera a conexão única cacheada via Resource
    db_manager = st.session_state.get('db_manager') 

    @st.cache_data(ttl=600, max_entries=10) # Limita cache para poupar RAM
    def carregar_patrimonio(uid):
        # Aqui você faria a query no banco usando db_manager
        return 150000.00 

    total = carregar_patrimonio(user_id)
    
    st.info(f"Seu patrimônio total consolidado: **R$ {total:,.2f}**")

    # Gráficos pesados (Plotly/Altair) devem ser gerados dentro de funções cacheadas
    import pandas as pd
    import plotly.express as px

    @st.cache_data
    def gerar_grafico_alocacao():
        df = pd.DataFrame({
            "Classe": ["Ações", "FIIs", "Renda Fixa"],
            "Valor": [50000, 30000, 70000]
        })
        return px.pie(df, values='Valor', names='Classe', title="Alocação de Ativos")

    fig = gerar_grafico_alocacao()
    st.plotly_chart(fig, use_container_width=True)
    
