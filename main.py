import streamlit as st
import streamlit_authenticator as stauth
from config.settings import settings

# 1. Configuração da Página (Sempre o primeiro comando)
st.set_page_config(page_title="Igorbarbo Private", layout="wide")

# 2. Inicialização do Banco de Dados como Recurso
@st.cache_resource
def get_db_manager():
    from database.repository import DatabaseManager
    manager = DatabaseManager()
    manager._init_database()
    manager.backup()
    return manager

db_manager = get_db_manager()

# 3. Cache de Credenciais para evitar consultas constantes ao disco
@st.cache_data(ttl=600)
def carregar_credenciais_autenticacao():
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT username, nome, senha_hash FROM usuarios")
        rows = cursor.fetchall()
    return {"usernames": {r['username']: {"name": r['nome'], "password": r['senha_hash']} for r in rows}}

# 4. Configurar Autenticador
authenticator = stauth.Authenticate(
    carregar_credenciais_autenticacao(),
    "invest_app_cookie",
    settings.COOKIE_KEY,
    30
)

authenticator.login()

if st.session_state["authentication_status"]:
    # Sidebar e Navegação
    st.sidebar.title("💎 IGORBARBO PRIVATE")
    authenticator.logout('Sair', 'sidebar')
    
    menu = st.sidebar.radio("Navegação", [
        "🏠 Dashboard", "💰 Preço Teto", "⚙️ Gestão"
    ])

    # 5. Roteamento com Lazy Loading (Importação sob demanda)
    if menu == "🏠 Dashboard":
        from views.dashboard import show_dashboard
        show_dashboard(st.session_state["username"])
        
    elif menu == "💰 Preço Teto":
        from views.preco_teto import show_preco_teto
        show_preco_teto(st.session_state["username"])
        
    elif menu == "⚙️ Gestão":
        from views.gestao import show_gestao
        show_gestao(st.session_state["username"])

elif st.session_state["authentication_status"] is False:
    st.error('Usuário ou senha incorretos')
else:
    st.warning('Por favor, faça o login')
    
