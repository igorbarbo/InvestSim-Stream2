import streamlit as st

st.title("📂 Minha Carteira")
st.write("Gerencie seus ativos aqui.")

# Exemplo simples de tabela
ativos = {"Ativo": ["PETR4", "VALE3", "CDB"], "Qtd": [100, 50, 1]}
st.table(ativos)
