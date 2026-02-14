import streamlit_authenticator as stauth
import sqlite3

def carregar_credenciais():
    conn = sqlite3.connect('data/invest_v10.db')
    c = conn.cursor()
    try:
        c.execute("SELECT username, nome, senha_hash FROM usuarios")
        rows = c.fetchall()
    except:
        rows = []
    finally:
        conn.close()
    
    cred = {"usernames": {}}
    for r in rows:
        cred["usernames"][r[0]] = {"name": r[1], "password": r[2]}
    return cred

def criar_authenticator():
    cred = carregar_credenciais()
    return stauth.Authenticate(cred, "invest_v10_cookie", "auth_key_123", 30)
