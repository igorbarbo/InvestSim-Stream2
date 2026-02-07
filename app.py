import streamlit as st
from streamlit_gsheets import GSheetsConnection

st.title("Teste de Conexão Direta")

try:
    # Tenta conectar usando os Secrets
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read()
    
    st.success("Conectado!")
    st.write("Aqui estão os dados da sua planilha:")
    st.dataframe(df)
except Exception as e:
    st.error(f"Erro detalhado: {e}")
    
