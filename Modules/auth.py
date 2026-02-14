# Modules/auth.py
import sqlite3
import streamlit as st
import streamlit_authenticator as stauth

def carregar_credenciais():
    """Carrega usuários do banco e retorna no formato do streamlit-authenticator."""
    conn = sqlite3.connect('invest_v8.db')
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
    # Gere uma chave secreta aleatória (use secrets.token_hex(16) em produção)
    COOKIE_KEY = "sua_chave_secreta_aqui_mude_isso"
    
    authenticator = stauth.Authenticate(
        credentials,
        "invest_app_cookie",
        COOKIE_KEY,
        30  # dias de expiração
    )
    return authenticator
