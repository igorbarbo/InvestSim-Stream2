import sqlite3
import os

def connect_db():
    if not os.path.exists('data'):
        os.makedirs('data')
    return sqlite3.connect('data/invest_v10.db', check_same_thread=False)

def init_db():
    conn = connect_db()
    c = conn.cursor()
    # Tabela de Usuários
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios 
                 (username TEXT PRIMARY KEY, nome TEXT, senha_hash TEXT)''')
    # Tabela de Ativos vinculada ao user_id
    c.execute('''CREATE TABLE IF NOT EXISTS ativos 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, 
                  ticker TEXT, qtd REAL, pm REAL, setor TEXT,
                  FOREIGN KEY(user_id) REFERENCES usuarios(username))''')
    # Tabela de Alertas
    c.execute('''CREATE TABLE IF NOT EXISTS alertas 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, 
                  ticker TEXT, preco_alvo REAL, tipo TEXT)''')
    conn.commit()
    conn.close()
    
