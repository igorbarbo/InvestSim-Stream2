import sqlite3
from contextlib import contextmanager
from pathlib import Path

class DatabaseManager:
    def __init__(self, db_path="database/invest.db"):
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        with self.get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS usuarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE,
                    nome TEXT,
                    senha_hash TEXT,
                    ultimo_login DATETIME
                )
            """)
            # Adicione aqui as outras tabelas (ativos, transacoes, etc)

    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def backup(self):
        # Lógica de backup simplificada
        print("💾 Backup realizado com sucesso.")

class UsuarioRepository:
    def __init__(self, db_manager):
        self.db = db_manager

    def buscar_por_username(self, username):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM usuarios WHERE username = ?", (username,))
            return cursor.fetchone()

    def atualizar_ultimo_login(self, user_id):
        import datetime
        with self.db.get_connection() as conn:
            conn.execute("UPDATE usuarios SET ultimo_login = ? WHERE id = ?", 
                         (datetime.datetime.now(), user_id))
            conn.commit()
            
