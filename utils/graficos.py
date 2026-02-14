# utils/graficos.py
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from typing import Optional
from services.preco_service import DadosAtivo

class GraficoService:
    """Serviço para geração de gráficos padronizados."""
    
    @staticmethod
    def historico_precos(dados: DadosAtivo, titulo: str = None) -> Optional[go.Figure]:
        """Gera gráfico de histórico com faixa de normalidade."""
        if dados.status != "ok" or dados.historico.empty:
            return None
        
        hist = dados.historico
        adj_close = hist['Adj Close']
        media_12m = dados.preco_medio_12m
        p20 = dados.percentil_20
        p80 = dados.percentil_80
        
        fig = go.Figure()
        
        # Linha de preço ajustado
        fig.add_trace(go.Scatter(
            x=hist.index, y=adj_close,
            mode='lines', name='Preço Ajustado',
            line=dict(color='#D4AF37', width=2)
        ))
        
        # Média 12 meses
        fig.add_trace(go.Scatter(
            x=hist.index, y=[media_12m]*len(hist),
            mode='lines', name='Média 12m',
            line=dict(color='white', width=1, dash='dash')
        ))
        
        # Faixa de normalidade (20% a 80%)
        fig.add_hrect(
            y0=p20, y1=p80,
            fillcolor="green", opacity=0.1,
            line_width=0, name="Faixa Normal (20-80%)"
        )
        
        # Linha do preço atual
        cor_status = "#00FF00" if dados.preco_atual < media_12m else "#FF4444"
        fig.add_hline(
            y=dados.preco_atual,
            line_dash="dot",
            line_color=cor_status,
            annotation_text=f"Atual: R$ {dados.preco_atual:.2f}",
            annotation_position="top right"
        )
        
        fig.update_layout(
            title=titulo or f"{dados.ticker} - Histórico de Preços",
            yaxis_title="Preço (R$)",
            xaxis_title="Data",
            height=400,
            showlegend=True,
            plot_bgcolor='#0F1116',
            paper_bgcolor='#0F1116',
            font=dict(color='white')
        )
        
        return fig
    
    @staticmethod
    def pizza(valores, nomes, titulo: str, hole: float = 0.5):
        """Gráfico de pizza padronizado."""
        fig = px.pie(
            values=valores, names=nomes,
            title=titulo, hole=hole,
            color_discrete_sequence=px.colors.sequential.Gold
        )
        return fig
    
    @staticmethod
    def linha(df: pd.DataFrame, x: str, y: str, titulo: str, cor: str = '#D4AF37'):
        """Gráfico de linha simples."""
        fig = px.line(df, x=x, y=y, title=titulo)
        fig.update_traces(line_color=cor, line_width=3)
        return fig
