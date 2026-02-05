import streamlit as st

def display_main_metrics(total_bruto, total_real, investido_total):
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("💰 Patrimônio Bruto", f"R$ {total_bruto:,.2f}")
    with col2:
        perda = total_real - total_bruto
        st.metric("🛒 Poder de Compra", f"R$ {total_real:,.2f}", 
                  delta=f"R$ {perda:,.2f} (Inflação)", delta_color="inverse")
    with col3:
        juros = total_bruto - investido_total
        st.metric("📈 Ganho em Juros", f"R$ {juros:,.2f}")
      
