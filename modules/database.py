import sqlite3
import os

def connect_db():
    """Conecta ao banco de dados v10 e garante que a pasta data exista."""
    if not os.path.exists('data'):
        os.makedirs('data')
    return sqlite3.connect('data/invest_v10.db', check_same_thread=False)

def init_db():
    """Inicializa as tabelas necessárias para o sistema multiusuário."""
    conn = connect_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios 
                 (username TEXT PRIMARY KEY, nome TEXT, senha_hash TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS ativos 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, 
                  ticker TEXT, qtd REAL, pm REAL, setor TEXT)''')
    conn.commit()
    conn.close()

def salvar_ativo(user_id, ticker, qtd, pm, setor):
    """Salva um novo ativo vinculado ao ID do usuário logado."""
    conn = connect_db()
    c = conn.cursor()
    c.execute("INSERT INTO ativos (user_id, ticker, qtd, pm, setor) VALUES (?, ?, ?, ?, ?)",
              (user_id, ticker.upper(), qtd, pm, setor))
    conn.commit()
    conn.close()
  
