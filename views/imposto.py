# views/imposto.py
import streamlit as st

def show_imposto(user_id):
    st.title("📝 Imposto de Renda")
    
    tab1, tab2, tab3 = st.tabs(["📊 Venda de Ações", "🏢 FIIs", "📋 Resumo Anual"])
    
    with tab1:
        st.write("### Simulador de IR - Venda de Ações")
        col1, col2, col3 = st.columns(3)
        with col1:
            acao = st.text_input("Ativo vendido", "PETR4").upper()
            qtd = st.number_input("Quantidade vendida", min_value=0.0, value=100.0)
        with col2:
            preco_compra = st.number_input("Preço médio de compra (R$)", min_value=0.01, value=30.0)
            preco_venda = st.number_input("Preço de venda (R$)", min_value=0.01, value=35.0)
        with col3:
            total_vendas_mes = st.number_input("Total vendido no mês (R$)", min_value=0.0, value=15000.0)
        
        custo = qtd * preco_compra
        venda = qtd * preco_venda
        lucro = venda - custo
        
        if lucro > 0 and total_vendas_mes > 20000:
            ir = lucro * 0.15
            st.error(f"IR devido: R$ {ir:,.2f}")
            with st.expander("Código DARF"):
                st.code(f"""
                DARF - Código 6015
                Valor: R$ {ir:.2f}
                Vencimento: Último dia útil do mês seguinte
                """)
        else:
            st.success("✅ ISENTO de IR")
    
    with tab2:
        st.write("### Imposto sobre FIIs")
        col1, col2 = st.columns(2)
        with col1:
            dividendos = st.number_input("Dividendos recebidos (R$)", min_value=0.0, value=500.0)
        with col2:
            lucro_fii = st.number_input("Lucro com vendas (R$)", min_value=0.0, value=0.0)
        ir = (dividendos + lucro_fii) * 0.20
        if ir > 0:
            st.error(f"IR sobre FIIs: R$ {ir:,.2f}")
