import pandas as pd
import streamlit as st

from logic.investment import simulate_investment
from logic.returns import real_return
from components.cards import display_main_metrics

st.title("Simulador de Investimentos")

initial_amount = st.number_input("Valor inicial (R$):", value=1000.0)
interest_rate = st.number_input("Taxa de retorno anual (%):", value=5.0) / 100
years = st.number_input("Número de anos:", value=10, step=1)
inflation_rate = st.number_input("Inflação anual (%):", value=3.0) / 100

# Simulação
future_value = simulate_investment(initial_amount, interest_rate, years)
real_future_value = real_return(future_value, interest_rate, inflation_rate)

# Exibir resultados
display_main_metrics(future_value, real_future_value)
