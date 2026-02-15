import streamlit as st

def show_preco_teto(user_id):
    st.title("💰 Calculadora de Preço Teto")
    st.subheader("Metodologias Bazin e Graham")

    # Importação local do service para economizar memória (Lazy Loading)
    from services.preco_service import PrecoService
    
    ticker = st.text_input("Digite o Ticker (ex: BBAS3):").upper()

    if ticker:
        # O uso de cache no service impede que a API te bloqueie (Fair-use)
        preco_atual = PrecoService.buscar_cotacao(ticker)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Preço Atual", f"R$ {preco_atual:.2f}")

        # Exemplo de lógica de cálculo com Cache para evitar reprocessamento
        @st.cache_data(ttl=3600)  # Dados de dividendos mudam pouco, cache de 1h
        def calcular_bazin(ticker_ativo):
            # Simulando busca de dividendo médio (Service deve buscar isso)
            div_medio = 2.50 
            return div_medio / 0.06

        teto_bazin = calcular_bazin(ticker)
        
        with col2:
            st.metric("Teto Bazin (6%)", f"R$ {teto_bazin:.2f}")
            
        with col3:
            margem = ((teto_bazin / preco_atual) - 1) * 100 if preco_atual > 0 else 0
            st.metric("Margem de Segurança", f"{margem:.2f}%")

        if preco_atual < teto_bazin:
            st.success(f"✅ {ticker} está abaixo do preço teto!")
        else:
            st.warning(f"⚠️ {ticker} está acima do preço teto.")
            
