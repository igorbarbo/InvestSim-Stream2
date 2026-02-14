import streamlit as st
import pandas as pd
import sqlite3
import streamlit_authenticator as stauth
from Modules.database import init_db, connect_db, salvar_ativo
from Modules.auth import criar_authenticator
from Modules.analise import pegar_preco, analisar_preco_ativo, calcular_bazin

# Configuração
st.set_page_config(page_title="Igorbarbo V10 Ultimate", layout="wide")
init_db()

# --- SISTEMA DE LOGIN ---
authenticator = criar_authenticator()
authenticator.login(location='main')

if st.session_state["authentication_status"]:
    # Variáveis de Sessão
    user = st.session_state["username"]
    name = st.session_state["name"]
    
    # Sidebar
    st.sidebar.title(f"💎 {name}")
    menu = st.sidebar.radio("Navegação", ["🏠 Dashboard", "🎯 Assistente", "💰 Preço Teto", "⚙️ Gestão"])
    authenticator.logout('Sair', 'sidebar')

    # --- PÁGINAS ---
    if menu == "🏠 Dashboard":
        st.title("📊 Minha Carteira")
        conn = connect_db()
        df = pd.read_sql_query(f"SELECT * FROM ativos WHERE user_id='{user}'", conn)
        conn.close()

        if not df.empty:
            # Resumo rápido
            col1, col2 = st.columns(2)
            df['Preço Atual'] = df['ticker'].apply(pegar_preco)
            df['Patrimônio'] = df['qtd'] * df['Preço Atual']
            total = df['Patrimônio'].sum()
            col1.metric("Patrimônio Total", f"R$ {total:,.2f}")
            st.dataframe(df, use_container_width=True)
        else:
            st.info("Sua carteira está vazia.")

    elif menu == "🎯 Assistente":
        st.title("🎯 Assistente de Alocação")
        t = st.text_input("Analise um Ticker (ex: PETR4)")
        if t:
            status, cor, desc, score = analisar_preco_ativo(t)
            st.markdown(f"<h2 style='color:{cor}'>{status}</h2>", unsafe_allow_html=True)
            st.info(desc)

    elif menu == "⚙️ Gestão":
        st.title("⚙️ Adicionar Ativos")
        with st.form("add"):
            c1, c2, c3, c4 = st.columns(4)
            tick = c1.text_input("Ticker")
            quant = c2.number_input("Quantidade", min_value=0.0)
            p_m = c3.number_input("Preço Médio", min_value=0.0)
            seto = c4.selectbox("Setor", ["Ações", "FIIs", "Renda Fixa"])
            if st.form_submit_button("Salvar"):
                salvar_ativo(user, tick, quant, p_m, seto)
                st.success("Salvo!")

elif st.session_state["authentication_status"] is False:
    st.error("Usuário/Senha incorretos.")
    # Opção de criar usuário se o banco estiver vazio
    if st.button("Criar Usuário Admin"):
        conn = connect_db()
        h = stauth.Hasher(["1234"]).generate()[0]
        conn.execute("INSERT OR IGNORE INTO usuarios VALUES ('admin', 'Igor Barbo', ?)", (h,))
        conn.commit()
        st.success("Usuário 'admin' com senha '1234' criado!")

elif st.session_state["authentication_status"] is None:
    st.warning("Acesse com seu usuário e senha.")
    
