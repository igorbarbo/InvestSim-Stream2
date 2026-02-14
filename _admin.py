import sqlite3
import streamlit_authenticator as stauth
import os

# 1. Garante que a pasta data existe
if not os.path.exists('data'):
    os.makedirs('data')

def setup_primeiro_usuario():
    # Conecta ao banco (ajustado para o caminho da sua nova estrutura)
    conn = sqlite3.connect('data/invest_v10.db')
    c = conn.cursor()

    # 2. Cria a tabela de usuários se não existir
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  username TEXT UNIQUE, 
                  nome TEXT, 
                  senha_hash TEXT)''')

    # 3. Define seus dados de acesso
    nome = "Igor Barbo"
    usuario = "admin"
    senha_plana = "1234" # Esta é a senha que você digitará no site

    # 4. Gera o HASH da senha (segurança obrigatória)
    senha_hash = stauth.Hasher([senha_plana]).generate()[0]

    try:
        # 5. Insere o usuário no banco
        c.execute("INSERT INTO usuarios (username, nome, senha_hash) VALUES (?, ?, ?)", 
                  (usuario, nome, senha_hash))
        conn.commit()
        print(f"✅ Usuário '{usuario}' criado com sucesso!")
    except sqlite3.IntegrityError:
        print(f"⚠️ O usuário '{usuario}' já existe no banco de dados.")
    
    conn.close()

if __name__ == "__main__":
    setup_primeiro_usuario()
  
