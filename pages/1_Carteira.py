import streamlit as st
from logic.investment import obter_taxa_cenario

# ===============================
# CONTROLE DE ESTADO (OBRIGATÓRIO)
# ===============================
if "perfil" not in st.session_state:
    st.session_state.perfil = "Conservador"

if "taxa" not in st.session_state:
    st.session_state.taxa = obter_taxa_cenario(st.session_state.perfil)import streamlit as st

st.title("📊 Carteira de Investimentos")

st.write("Defina a distribuição da sua carteira:")

renda_fixa = st.slider("Renda Fixa (%)", 0, 100, 40)
acoes = st.slider("Ações (%)", 0, 100, 40)
cripto = st.slider("Cripto (%)", 0, 100, 20)

total = renda_fixa + acoes + cripto

if total != 100:
    st.error(f"A soma precisa ser 100%. Atualmente: {total}%")
else:
    st.success("Carteira válida!")

st.markdown("---")
st.write("📌 Distribuição atual:")
st.write({
    "Renda Fixa": f"{renda_fixa}%",
    "Ações": f"{acoes}%",
    "Cripto": f"{cripto}%"
})
