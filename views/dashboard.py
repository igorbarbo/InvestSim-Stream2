import streamlit as st
from database.repository import AtivoRepository
from services.preco_service import PrecoService

def show_dashboard(user_id):
    st.title("🏛️ Seu Patrimônio")
    repo = AtivoRepository()
    serv = PrecoService()
    
    ativos = repo.carregar_por_usuario(user_id)
    if not ativos:
        st.info("Carteira vazia.")
        return
    
    tickers = [a['ticker'] for a in ativos]
    precos = serv.buscar_precos_batch(tickers)
    
    for a in ativos:
        p_atual = precos.get(a['ticker'], 0)
        st.metric(a['ticker'], f"R$ {p_atual:.2f}", f"{a['qtd']} cotas")
      
