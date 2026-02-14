import sqlite3
import os

def connect_db():
    if not os.path.exists('data'):
        os.makedirs('data')
    return sqlite3.connect('data/invest_v10.db', check_same_thread=False)

def init_db():
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
    conn = connect_db()
    c = conn.cursor()
    c.execute("INSERT INTO ativos (user_id, ticker, qtd, pm, setor) VALUES (?, ?, ?, ?, ?)",
              (user_id, ticker.upper(), qtd, pm, setor))
    conn.commit()
    conn.close()
    
