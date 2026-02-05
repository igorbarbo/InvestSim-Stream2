import pandas as pd
import streamlit as st
import altair as alt

from logic.investment import simulate_investment
from logic.returns import real_return
from components.cards import display_main_metrics

st.title("Simulador de Investimentos")

# ------------------------------
# INPUTS DO USUÁRIO
# ------------------------------
initial_amount = st.number_input("Valor inicial (R$):", value=1000.0)
interest_rate = st.number_input("Taxa de retorno anual (%):", value=5.0) / 100
years = st.number_input("Número de anos:", value=10, step=1)
inflation_rate = st.number_input("Inflação anual (%):", value=3.0) / 100

# ------------------------------
# SIMULAÇÃO ANUAL
# ------------------------------
years_list = list(range(1, years + 1))
nominal_values = [simulate_investment(initial_amount, interest_rate, y) for y in years_list]
real_values = [real_return(val, interest_rate, inflation_rate) for val in nominal_values]

# ------------------------------
# EXIBIR RESULTADOS
# ------------------------------
future_value = nominal_values[-1]
real_future_value = real_values[-1]

display_main_metrics(future_value, real_future_value)

# ------------------------------
# GRÁFICO INTERATIVO
# ------------------------------
df = pd.DataFrame({
    'Ano': years_list,
    'Valor Nominal': nominal_values,
    'Valor Real': real_values
})

# Transformar dados para Altair
df_melted = df.melt('Ano', var_name='Tipo', value_name='Valor')

chart = alt.Chart(df_melted).mark_line(point=True).encode(
    x='Ano',
    y='Valor',
    color='Tipo',
    tooltip=['Ano', 'Tipo', alt.Tooltip('Valor', format=".2f")]
).interactive()

st.subheader("Evolução do Investimento ao Longo dos Anos")
st.altair_chart(chart, use_container_width=True)
