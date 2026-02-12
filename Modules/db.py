import sqlite3
import pandas as pd
import datetime

DB_NAME = "terminal_v6_pro.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    conn.execute('''CREATE TABLE IF NOT EXISTS assets 
                 (ticker TEXT PRIMARY KEY, qtd REAL, pm REAL, data_alt TIMESTAMP)''')
    conn.commit()
    conn.close()

def get_assets():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM assets", conn)
    conn.close()
    return df

def add_asset(ticker, qtd, pm):
    conn = sqlite3.connect(DB_NAME)
    conn.execute("""INSERT OR REPLACE INTO assets (ticker, qtd, pm, data_alt) 
                 VALUES (?, ?, ?, ?)""", (ticker.upper(), qtd, pm, datetime.datetime.now()))
    conn.commit()
    conn.close()
  
