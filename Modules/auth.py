import sqlite3
import streamlit_authenticator as stauth
import os

def carregar_credenciais():
    """Carrega usuários do banco e retorna no formato do streamlit-authenticator."""
    # 1. Garante que a pasta 'data' existe para evitar o OperationalError
    if not os.path.exists('data'):
        os.makedirs('data')
        
    # 2. Tenta conectar ao banco
    db_path = 'data/invest_v10.db'
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    try:
        c.execute("SELECT username, nome, senha_hash FROM usuarios")
        usuarios = c.fetchall()
    except sqlite3.OperationalError:
        # Se a tabela não existir, retorna credenciais vazias em vez de travar o app
        return {"usernames": {}}
    finally:
        conn.close()

    credentials = {"usernames": {}}
    for u in usuarios:
        credentials["usernames"][u[0]] = {
            "name": u[1],
            "password": u[2]
        }
    return credentials
    
