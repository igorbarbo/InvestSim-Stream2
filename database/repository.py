import sqlite3
import shutil
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from config.settings import settings

class DatabaseManager:
    def __init__(self, db_path: str = None):
        self.db_path = db_path or settings.DB_PATH
        self._init_database()

    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def _init_database(self):
        with self.get_connection() as conn:
            conn.execute("CREATE TABLE IF NOT EXISTS usuarios (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, nome TEXT, senha_hash TEXT, last_login TIMESTAMP)")
            conn.execute("CREATE TABLE IF NOT EXISTS ativos (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, ticker TEXT, qtd REAL, pm REAL, setor TEXT, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
            conn.execute("CREATE TABLE IF NOT EXISTS logs_auditoria (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, acao TEXT, detalhes TEXT, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP, ip_address TEXT)")

    def backup(self):
        Path(settings.BACKUP_DIR).mkdir(exist_ok=True)
        backup_path = Path(settings.BACKUP_DIR) / f"invest_{datetime.now().strftime('%Y%m%d')}.db"
        shutil.copy2(self.db_path, backup_path)

class AtivoRepository:
    def __init__(self, db_manager=None):
        self.db = db_manager or DatabaseManager()

    def carregar_por_usuario(self, user_id):
        with self.db.get_connection() as conn:
            return [dict(row) for row in conn.execute("SELECT * FROM ativos WHERE user_id = ?", (user_id,)).fetchall()]

    def salvar(self, ativo, user_id):
        with self.db.get_connection() as conn:
            conn.execute("INSERT INTO ativos (user_id, ticker, qtd, pm, setor) VALUES (?,?,?,?,?)", 
                         (user_id, ativo.ticker, float(ativo.quantidade), float(ativo.preco_medio), ativo.setor))
          
