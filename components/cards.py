import streamlit as st

def display_main_metrics(future_value, real_future_value):
    st.subheader("Resultados da Simulação")
    st.write(f"💰 Valor Futuro Nominal: R$ {future_value:,.2f}")
    st.write(f"📉 Valor Futuro Real (descontando inflação): R$ {real_future_value:,.2f}")
