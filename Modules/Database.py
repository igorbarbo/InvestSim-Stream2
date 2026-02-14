# Modules/database.py
import sqlite3
import pandas as pd
import streamlit as st

DB_PATH = 'invest_v8.db'

def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    """Cria as tabelas necessárias, se não existirem."""
    conn = get_connection()
    c = conn.cursor()
    # Tabela de usuários
    c.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            nome TEXT NOT NULL,
            senha_hash TEXT NOT NULL
        )
    ''')
    # Tabela de ativos
    c.execute('''
        CREATE TABLE IF NOT EXISTS ativos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            ticker TEXT NOT NULL,
            qtd REAL NOT NULL,
            pm REAL NOT NULL,
            setor TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES usuarios(id)
        )
    ''')
    # Tabela de metas de alocação
    c.execute('''
        CREATE TABLE IF NOT EXISTS metas_alocacao (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            classe TEXT NOT NULL,
            percentual REAL NOT NULL,
            FOREIGN KEY(user_id) REFERENCES usuarios(id)
        )
    ''')
    # Tabela de alertas
    c.execute('''
        CREATE TABLE IF NOT EXISTS alertas (
            id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            ticker TEXT NOT NULL,
            tipo TEXT NOT NULL,
            preco REAL NOT NULL,
            ativo BOOL NOT NULL,
            criado_em TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES usuarios(id)
        )
    ''')
    conn.commit()
    conn.close()

# -------------------- Ativos --------------------
def salvar_ativo(user_id, ticker, qtd, pm, setor):
    if not ticker or len(ticker.strip()) < 2:
        st.error("❌ Ticker inválido!")
        return False
    if qtd <= 0:
        st.error("❌ Quantidade deve ser maior que zero!")
        return False
    if pm <= 0:
        st.error("❌ Preço médio deve ser maior que zero!")
        return False
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute(
            "INSERT INTO ativos (user_id, ticker, qtd, pm, setor) VALUES (?, ?, ?, ?, ?)",
            (user_id, ticker.upper().strip(), float(qtd), float(pm), setor)
        )
        conn.commit()
        conn.close()
        st.success(f"✅ {ticker.upper()} salvo!")
        return True
    except Exception as e:
        st.error(f"❌ Erro ao salvar: {str(e)}")
        return False

def excluir_ativo(user_id, ticker):
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute("DELETE FROM ativos WHERE user_id = ? AND ticker = ?", (user_id, ticker))
        conn.commit()
        conn.close()
        st.success(f"✅ {ticker} excluído!")
        return True
    except Exception as e:
        st.error(f"❌ Erro ao excluir: {str(e)}")
        return False

def atualizar_ativo(user_id, ticker, qtd, pm, setor):
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute(
            "UPDATE ativos SET qtd=?, pm=?, setor=? WHERE user_id=? AND ticker=?",
            (float(qtd), float(pm), setor, user_id, ticker.upper().strip())
        )
        conn.commit()
        conn.close()
        st.success(f"✅ {ticker} atualizado!")
        return True
    except Exception as e:
        st.error(f"❌ Erro ao atualizar: {str(e)}")
        return False

def carregar_ativos(user_id):
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM ativos WHERE user_id = ?", conn, params=(user_id,))
    conn.close()
    return df

# -------------------- Metas --------------------
def salvar_metas(user_id, metas):
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute("DELETE FROM metas_alocacao WHERE user_id = ?", (user_id,))
        for classe, percentual in metas.items():
            c.execute(
                "INSERT INTO metas_alocacao (user_id, classe, percentual) VALUES (?, ?, ?)",
                (user_id, classe, percentual)
            )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"❌ Erro ao salvar metas: {str(e)}")
        return False

def carregar_metas(user_id):
    try:
        conn = get_connection()
        df = pd.read_sql_query("SELECT classe, percentual FROM metas_alocacao WHERE user_id = ?", conn, params=(user_id,))
        conn.close()
        return dict(zip(df['classe'], df['percentual']))
    except:
        return {}

# -------------------- Alertas --------------------
def salvar_alerta(user_id, ticker, tipo, preco):
    try:
        conn = get_connection()
        c = conn.cursor()
        alerta_id = f"{ticker}_{tipo}_{preco}_{datetime.now().timestamp()}"
        c.execute(
            "INSERT INTO alertas (id, user_id, ticker, tipo, preco, ativo, criado_em) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (alerta_id, user_id, ticker, tipo, preco, 1, datetime.now().strftime('%d/%m/%Y %H:%M'))
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"❌ Erro ao salvar alerta: {str(e)}")
        return False

def carregar_alertas(user_id):
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT id, ticker, tipo, preco, ativo, criado_em FROM alertas WHERE user_id = ? AND ativo = 1", (user_id,))
        rows = c.fetchall()
        conn.close()
        alertas = {}
        for r in rows:
            alertas[r[0]] = {
                'ticker': r[1],
                'tipo': r[2],
                'preco': r[3],
                'ativo': bool(r[4]),
                'criado_em': r[5]
            }
        return alertas
    except:
        return {}

def excluir_alerta(alerta_id):
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute("DELETE FROM alertas WHERE id = ?", (alerta_id,))
        conn.commit()
        conn.close()
        return True
    except:
        return False

# -------------------- Usuários --------------------
def criar_usuario(username, nome, senha_plana):
    from streamlit_authenticator import Hasher
    hashed = Hasher([senha_plana]).generate()[0]
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute(
            "INSERT INTO usuarios (username, nome, senha_hash) VALUES (?, ?, ?)",
            (username, nome, hashed)
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Erro ao criar usuário: {e}")
        return False

def buscar_usuario_por_username(username):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, username, nome, senha_hash FROM usuarios WHERE username = ?", (username,))
    row = c.fetchone()
    conn.close()
    if row:
        return {'id': row[0], 'username': row[1], 'nome': row[2], 'senha_hash': row[3]}
    return None
