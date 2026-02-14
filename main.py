import streamlit as st
import streamlit_authenticator as stauth
from config.settings import settings
from database.repository import DatabaseManager, AtivoRepository
from views.dashboard import show_dashboard

st.set_page_config(page_title="Igorbarbo Private", layout="wide")

db = DatabaseManager()

# Autenticação Simplificada (Exemplo)
creds = {"usernames": {settings.ADMIN_USERNAME: {"name": "Admin", "password": stauth.Hasher.hash(settings.ADMIN_PASSWORD)}}}
auth = stauth.Authenticate(creds, "cookie_name", settings.COOKIE_KEY)

name, status, username = auth.login("Login", "main")

if status:
    auth.logout("Sair", "sidebar")
    user_id = 1 # No sistema real, busque o ID no banco
    
    menu = st.sidebar.radio("Navegação", ["Dashboard", "Gestão", "Análise"])
    
    if menu == "Dashboard":
        show_dashboard(user_id)
else:
    st.warning("Aguardando login...")
  
