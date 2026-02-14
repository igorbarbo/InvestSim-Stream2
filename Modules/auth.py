import sqlite3
import streamlit_authenticator as stauth

def carregar_credenciais():
    """Carrega usuários do banco e retorna no formato do streamlit-authenticator."""
    # Atenção: Verifique se o nome é invest_v8.db ou invest_v10.db conforme conversamos
    conn = sqlite3.connect('data/invest_v10.db') 
    c = conn.cursor()
    c.execute("SELECT username, nome, senha_hash FROM usuarios")
    usuarios = c.fetchall()
    conn.close()

    credentials = {"usernames": {}}
    for u in usuarios:
        credentials["usernames"][u[0]] = {
            "name": u[1],
            "password": u[2]
        }
    return credentials

def criar_authenticator():
    """Cria e retorna o objeto authenticator."""
    credentials = carregar_credenciais()
    
    # Chave secreta para o cookie (mantenha fixa para não deslogar o usuário ao atualizar)
    COOKIE_KEY = "chave_super_secreta_123"

    authenticator = stauth.Authenticate(
        credentials,
        "invest_app_cookie",
        COOKIE_KEY,
        30  # Dias de expiração (A vírgula aqui é essencial)
    )
    return authenticator
    
