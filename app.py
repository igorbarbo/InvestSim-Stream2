import streamlit as st
import pandas as pd
import streamlit_authenticator as stauth
from modules.database import init_db, connect_db, salvar_ativo
from modules.auth import criar_authenticator
from modules.analise import analise_caro_barato, preco_teto_bazin
from modules.utils import gerar_grafico_setor, exportar_excel, calcular_risco_retorno
from modules.assistente import renderizar_assistente

st.set_page_config(page_title="Igorbarbo V10 Ultimate", layout="wide")
init_db()
auth = criar_authenticator()
auth.login(location='main')

if st.session_state.get("authentication_status"):
    user = st.session_state["username"]
    menu = st.sidebar.radio("Navegação", ["🏠 Dashboard", "🎯 Assistente", "💰 Bazin", "📈 Risco", "⚙️ Gestão"])
    auth.logout('Sair', 'sidebar')

    conn = connect_db()
    df = pd.read_sql_query(f"SELECT * FROM ativos WHERE user_id='{user}'", conn)
    conn.close()

    if menu == "🏠 Dashboard":
        st.title("📊 Painel de Controle")
        if not df.empty:
            df['Preço Atual'] = df['ticker'].apply(lambda x: analise_caro_barato(x)[3])
            df['Patrimônio'] = df['qtd'] * df['Preço Atual']
            st.metric("Patrimônio Total", f"R$ {df['Patrimônio'].sum():,.2f}")
            st.plotly_chart(gerar_grafico_setor(df))
            st.dataframe(df)
            st.download_button("Excel", exportar_excel(df), "carteira.xlsx")
        else: st.info("Carteira vazia.")

    elif menu == "🎯 Assistente":
        renderizar_assistente(user, salvar_ativo)

elif st.session_state.get("authentication_status") is False:
    st.error("Erro de login.")
    if st.button("Setup Admin"):
        conn = connect_db()
        h = stauth.Hasher.hash("1234")
        conn.execute("INSERT OR IGNORE INTO usuarios VALUES ('admin', 'Igor Barbo', ?)", (h,))
        conn.commit()
        st.success("Admin criado: senha 1234")
        
