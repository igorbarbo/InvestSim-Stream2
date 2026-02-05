import streamlit as st

def display_main_metrics(future_value, real_future_value):
    col1, col2 = st.columns(2)
    col1.metric("Valor Futuro (nominal)", f"R$ {future_value:,.2f}")
    col2.metric("Valor Futuro (ajustado pela inflação)", f"R$ {real_future_value:,.2f}")
