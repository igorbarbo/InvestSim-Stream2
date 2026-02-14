# services/auditoria_service.py
import streamlit as st
from datetime import datetime
from database.repository import DatabaseManager
from models.ativo import LogAuditoria
from config.settings import settings

class AuditoriaService:
    """Serviço para registro de logs de auditoria."""
    
    def __init__(self):
        self.db = DatabaseManager()
    
    def registrar(self, user_id: int, acao: str, detalhes: str = ""):
        """Registra uma ação do usuário no log."""
        if not settings.ENABLE_AUDIT_LOG:
            return
        
        try:
            ip = st.context.headers.get('X-Forwarded-For', 'desconhecido') if hasattr(st, 'context') else None
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO logs_auditoria (user_id, acao, detalhes, ip_address)
                    VALUES (?, ?, ?, ?)
                ''', (user_id, acao[:50], detalhes[:500], ip))
        except Exception as e:
            # Não interrompe a aplicação, apenas loga no console
            print(f"Erro ao registrar log: {e}")
