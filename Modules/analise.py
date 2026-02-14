# Modules/analise.py
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
import streamlit as st

# ============================================
# FUNÇÕES DE PREÇO
# ============================================

@st.cache_data(ttl=300)
def pegar_preco(ticker):
    """
    Busca preço atual do ativo.
    Retorna: (preco, status, mensagem)
    status pode ser 'ok', 'aviso' ou 'erro'.
    """
    try:
        # Se ticker terminar com número (ex: PETR4), adiciona .SA; senão, deixa como está (para ETFs americanos)
        if ticker[-1].isdigit():
            ticker_yf = f"{ticker}.SA"
        else:
            ticker_yf = ticker
        acao = yf.Ticker(ticker_yf)
        hist = acao.history(period="2d")
        
        if hist.empty:
            return None, "erro", "Sem dados disponíveis"
        
        preco = hist['Close'].iloc[-1]
        ultima_data = hist.index[-1].date()
        hoje = datetime.now().date()
        
        if ultima_data == hoje:
            return preco, "ok", "Atualizado"
        else:
            return preco, "aviso", f"Último: {ultima_data.strftime('%d/%m')}"
    except Exception as e:
        return None, "erro", str(e)

def pegar_preco_simples(ticker):
    """Versão simples que só retorna o preço (0 se falhar)."""
    preco, _, _ = pegar_preco(ticker)
    return preco if preco else 0.0

# ============================================
# DADOS HISTÓRICOS E ANÁLISE CARO/BARATO
# ============================================

@st.cache_data(ttl=3600)
def buscar_dados_historicos(ticker, periodo="5y"):
    """
    Busca dados históricos do ativo para análise.
    Retorna um dicionário com métricas ou None se falhar.
    """
    try:
        # Define o ticker correto para yfinance
        if ticker[-1].isdigit():
            ticker_yf = f"{ticker}.SA"
        else:
            ticker_yf = ticker
        acao = yf.Ticker(ticker_yf)
        hist = acao.history(period=periodo)
        
        # Se não houver dados no período solicitado, tenta "max"
        if hist.empty:
            hist = acao.history(period="max")
            if hist.empty:
                return None
        
        preco_atual = hist['Close'].iloc[-1]
        
        # Média 12 meses: se houver menos de 252 dias, usa todo o histórico disponível
        if len(hist) >= 252:
            preco_medio_12m = hist['Close'].tail(252).mean()
        else:
            preco_medio_12m = hist['Close'].mean()
        
        preco_medio_5y = hist['Close'].mean()
        
        percentil_20 = hist['Close'].quantile(0.20)
        percentil_80 = hist['Close'].quantile(0.80)
        
        minimo_5y = hist['Close'].min()
        maximo_5y = hist['Close'].max()
        
        # Variação anual (últimos 252 dias úteis)
        if len(hist) > 252:
            preco_1ano_atras = hist['Close'].iloc[-252]
            variacao_anual = (preco_atual / preco_1ano_atras - 1) * 100
        else:
            variacao_anual = 0
        
        # --- Cálculo de dividendos melhorado ---
        try:
            # Pega os últimos 24 meses de dividendos (para maior estabilidade)
            dividends = acao.dividends.tail(24)
            if not dividends.empty:
                # Soma dos dividendos dos últimos 12 meses (ou dos disponíveis)
                dividends_12m = dividends.tail(12).sum()
                # Se tiver menos de 12 meses, anualiza com base no período disponível
                if len(dividends) < 12:
                    # Média mensal * 12
                    dividends_12m = dividends.mean() * 12
                if preco_atual > 0:
                    dy = (dividends_12m / preco_atual) * 100
                else:
                    dy = None
            else:
                dy = None
        except Exception:
            dy = None
        
        return {
            'ticker': ticker,
            'preco_atual': preco_atual,
            'preco_medio_12m': preco_medio_12m,
            'preco_medio_5y': preco_medio_5y,
            'percentil_20': percentil_20,
            'percentil_80': percentil_80,
            'minimo_5y': minimo_5y,
            'maximo_5y': maximo_5y,
            'variacao_anual': variacao_anual,
            'dividend_yield': dy,
            'dados': hist
        }
    except Exception as e:
        return None

def analisar_preco_ativo(ticker, dados_historicos):
    """
    Analisa se o preço atual está caro ou barato baseado em dados históricos.
    Retorna: (status, mensagem, cor, explicacao, pontuacao)
    """
    if not dados_historicos:
        return ("neutro", "🔵 DADOS INSUFICIENTES", "#808080",
                "Não há dados históricos suficientes para análise. Isso é comum em ativos de renda fixa (Tesouro, CDB) ou em ativos recém-listados.", 0)
    
    preco = dados_historicos['preco_atual']
    media_12m = dados_historicos['preco_medio_12m']
    p20 = dados_historicos['percentil_20']
    p80 = dados_historicos['percentil_80']
    minimo = dados_historicos['minimo_5y']
    maximo = dados_historicos['maximo_5y']
    
    posicao_relativa = ((preco - minimo) / (maximo - minimo)) * 100 if maximo > minimo else 50
    
    pontuacao = 0
    motivos = []
    alerta_risco = ""  # para incluir mensagem extra se necessário
    
    # 1. Comparação com média 12 meses
    if preco < media_12m * 0.85:
        pontuacao -= 25
        motivos.append("📉 Preço 15% abaixo da média de 12 meses")
    elif preco < media_12m * 0.9:
        pontuacao -= 20
        motivos.append("📉 Preço 10% abaixo da média de 12 meses")
    elif preco < media_12m:
        pontuacao -= 10
        motivos.append("📉 Preço abaixo da média de 12 meses")
    elif preco > media_12m * 1.15:
        pontuacao += 25
        motivos.append("📈 Preço 15% acima da média de 12 meses")
    elif preco > media_12m * 1.1:
        pontuacao += 20
        motivos.append("📈 Preço 10% acima da média de 12 meses")
    elif preco > media_12m:
        pontuacao += 10
        motivos.append("📈 Preço acima da média de 12 meses")
    
    # 2. Comparação com percentis
    if preco < p20:
        pontuacao -= 30
        motivos.append("💰 Entre os 20% preços mais baixos dos últimos 5 anos")
    elif preco > p80:
        pontuacao += 30
        motivos.append("⚠️ Entre os 20% preços mais altos dos últimos 5 anos")
    
    # 3. Posição relativa na faixa histórica
    if posicao_relativa < 15:
        pontuacao -= 25
        motivos.append(f"🎯 Próximo da mínima histórica (R$ {minimo:.2f})")
    elif posicao_relativa < 30:
        pontuacao -= 15
        motivos.append("📊 Na faixa inferior da série histórica")
    elif posicao_relativa > 85:
        pontuacao += 25
        motivos.append(f"🔴 Próximo da máxima histórica (R$ {maximo:.2f})")
    elif posicao_relativa > 70:
        pontuacao += 15
        motivos.append("📊 Na faixa superior da série histórica")
    
    # 4. Variação anual
    if dados_historicos['variacao_anual'] < -20:
        pontuacao -= 20
        motivos.append(f"📉 Caiu {dados_historicos['variacao_anual']:.1f}% no último ano")
        if dados_historicos['variacao_anual'] < -50:
            alerta_risco = "\n\n⚠️ **ALERTA DE RISCO:** Queda superior a 50% no último ano. Verifique problemas fundamentais antes de investir."
    elif dados_historicos['variacao_anual'] < -10:
        pontuacao -= 10
        motivos.append(f"📉 Caiu {dados_historicos['variacao_anual']:.1f}% no último ano")
    elif dados_historicos['variacao_anual'] > 50:
        pontuacao += 25
        motivos.append(f"🚀 Subiu {dados_historicos['variacao_anual']:.1f}% no último ano")
    elif dados_historicos['variacao_anual'] > 30:
        pontuacao += 15
        motivos.append(f"🚀 Subiu {dados_historicos['variacao_anual']:.1f}% no último ano")
    
    # Construir explicação com base na pontuação
    if pontuacao <= -40:
        status = "oportunidade"
        mensagem = "🔥 OPORTUNIDADE! Muito barato"
        cor = "#00FF00"
        explicacao = "### ✅ OPORTUNIDADE DE COMPRA!\n\n"
        explicacao += "**Este ativo está muito barato comparado à sua história:**\n\n"
        for m in motivos[:4]:
            explicacao += f"• {m}\n"
        explicacao += f"\n📊 **Preço atual:** R$ {preco:.2f}\n"
        explicacao += f"📊 **Média 12m:** R$ {media_12m:.2f}\n"
        explicacao += f"📊 **Mínima 5 anos:** R$ {minimo:.2f}\n"
        explicacao += f"📊 **Máxima 5 anos:** R$ {maximo:.2f}\n"
        if dados_historicos['dividend_yield']:
            explicacao += f"💰 **Dividend Yield:** {dados_historicos['dividend_yield']:.2f}%\n"
        explicacao += f"\n💡 **RECOMENDAÇÃO:** COMPRAR - Ótimo ponto de entrada!"
        explicacao += alerta_risco
    elif pontuacao <= -20:
        status = "barato"
        mensagem = "👍 Barato - Bom momento"
        cor = "#90EE90"
        explicacao = "### ✅ PREÇO ATRATIVO\n\n"
        explicacao += "**Este ativo está abaixo da média histórica:**\n\n"
        for m in motivos[:3]:
            explicacao += f"• {m}\n"
        explicacao += f"\n📊 **Preço atual:** R$ {preco:.2f}\n"
        explicacao += f"📊 **Média 12m:** R$ {media_12m:.2f}\n"
        if dados_historicos['dividend_yield']:
            explicacao += f"💰 **Dividend Yield:** {dados_historicos['dividend_yield']:.2f}%\n"
        explicacao += f"\n💡 **RECOMENDAÇÃO:** Pode comprar - preço justo"
        explicacao += alerta_risco
    elif pontuacao <= 0:
        status = "neutro"
        mensagem = "⚖️ Preço justo"
        cor = "#D4AF37"
        explicacao = "### ⚖️ PREÇO JUSTO\n\n"
        explicacao += "**Este ativo está dentro da faixa histórica normal:**\n\n"
        for m in motivos[:2]:
            explicacao += f"• {m}\n"
        explicacao += f"\n📊 **Preço atual:** R$ {preco:.2f}\n"
        explicacao += f"📊 **Média 12m:** R$ {media_12m:.2f}\n"
        explicacao += f"\n💡 **RECOMENDAÇÃO:** Compra neutra - nem barato nem caro"
        explicacao += alerta_risco
    elif pontuacao <= 20:
        status = "atencao"
        mensagem = "⚠️ Atenção - Acima da média"
        cor = "#FFA500"
        explicacao = "### ⚠️ PREÇO ELEVADO\n\n"
        explicacao += "**Este ativo está acima da média histórica:**\n\n"
        for m in motivos[:3]:
            explicacao += f"• {m}\n"
        explicacao += f"\n📊 **Preço atual:** R$ {preco:.2f}\n"
        explicacao += f"📊 **Média 12m:** R$ {media_12m:.2f}\n"
        explicacao += f"📊 **Máxima 5 anos:** R$ {maximo:.2f}\n"
        explicacao += f"\n💡 **RECOMENDAÇÃO:** Comprar só se necessário - preço salgado"
        explicacao += alerta_risco
    else:
        status = "caro"
        mensagem = "❌ CARO! Evite comprar"
        cor = "#FF4444"
        explicacao = "### ❌ PREÇO CARO DEMAIS!\n\n"
        explicacao += "**Este ativo está muito caro comparado à sua história:**\n\n"
        for m in motivos[:4]:
            explicacao += f"• {m}\n"
        explicacao += f"\n📊 **Preço atual:** R$ {preco:.2f}\n"
        explicacao += f"📊 **Média 12m:** R$ {media_12m:.2f}\n"
        explicacao += f"📊 **Máxima 5 anos:** R$ {maximo:.2f}\n"
        if dados_historicos['dividend_yield']:
            explicacao += f"💰 **Dividend Yield:** {dados_historicos['dividend_yield']:.2f}%\n"
        preco_ideal = media_12m * 0.9
        explicacao += f"\n💡 **RECOMENDAÇÃO:** NÃO COMPRAR AGORA!\n"
        explicacao += f"   Espere o preço cair para pelo menos R$ {preco_ideal:.2f}"
        explicacao += alerta_risco
    
    return status, mensagem, cor, explicacao, pontuacao

def plotar_grafico_historico(dados_historicos, ticker):
    """Gera gráfico com análise de preço (linha do tempo com faixa de normalidade)."""
    if not dados_historicos:
        return None
    
    hist = dados_historicos['dados']
    preco_atual = dados_historicos['preco_atual']
    media_12m = dados_historicos['preco_medio_12m']
    p20 = dados_historicos['percentil_20']
    p80 = dados_historicos['percentil_80']
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=hist.index,
        y=hist['Close'],
        mode='lines',
        name='Preço',
        line=dict(color='#D4AF37', width=2)
    ))
    
    fig.add_trace(go.Scatter(
        x=hist.index,
        y=[media_12m] * len(hist),
        mode='lines',
        name='Média 12m',
        line=dict(color='white', width=1, dash='dash')
    ))
    
    fig.add_hrect(
        y0=p20, y1=p80,
        fillcolor="green",
        opacity=0.1,
        line_width=0,
        name="Faixa Normal (20-80%)"
    )
    
    cor_status = "#00FF00" if preco_atual < media_12m else "#FF4444"
    fig.add_hline(
        y=preco_atual,
        line_dash="dot",
        line_color=cor_status,
        annotation_text=f"Atual: R$ {preco_atual:.2f}",
        annotation_position="top right"
    )
    
    fig.update_layout(
        title=f"{ticker} - Histórico de Preços (5 anos)",
        yaxis_title="Preço (R$)",
        xaxis_title="Data",
        height=400,
        showlegend=True,
        plot_bgcolor='#0F1116',
        paper_bgcolor='#0F1116',
        font=dict(color='white')
    )
    
    return fig

# ============================================
# FUNÇÕES DE ANÁLISE AVANÇADA
# ============================================

def calcular_matriz_correlacao(tickers, periodo="1y"):
    """
    Calcula matriz de correlação entre os ativos.
    Retorna (correlacao_df, dados_df) ou (None, None) se insuficiente.
    """
    if len(tickers) < 2:
        return None, None
    
    dados = {}
    for ticker in tickers:
        try:
            if ticker[-1].isdigit():
                ticker_yf = f"{ticker}.SA"
            else:
                ticker_yf = ticker
            acao = yf.Ticker(ticker_yf)
            hist = acao.history(period=periodo)['Close']
            if not hist.empty:
                dados[ticker] = hist
        except:
            continue
    
    if len(dados) < 2:
        return None, None
    
    df = pd.DataFrame(dados)
    correlacao = df.pct_change().corr()
    
    return correlacao, df

def analisar_concentracao_setorial(df_ativos):
    """
    Analisa concentração por setor e retorna alertas.
    df_ativos deve ter colunas 'setor' e 'Patrimônio'.
    """
    if df_ativos.empty:
        return None, None
    
    total = df_ativos['Patrimônio'].sum()
    if total == 0:
        return None, None
    setores = df_ativos.groupby('setor')['Patrimônio'].sum() / total * 100
    
    alertas = []
    for setor, percentual in setores.items():
        if percentual > 50:
            alertas.append({
                'setor': setor,
                'percentual': percentual,
                'nivel': 'CRÍTICO',
                'cor': '#FF4444',
                'mensagem': f"🚨 PERIGO: {percentual:.1f}% em {setor}! Altíssima concentração!"
            })
        elif percentual > 30:
            alertas.append({
                'setor': setor,
                'percentual': percentual,
                'nivel': 'ALTO',
                'cor': '#FFA500',
                'mensagem': f"⚠️ Atenção: {percentual:.1f}% em {setor}. Muita exposição."
            })
        elif percentual > 20:
            alertas.append({
                'setor': setor,
                'percentual': percentual,
                'nivel': 'MÉDIO',
                'cor': '#D4AF37',
                'mensagem': f"📊 {percentual:.1f}% em {setor} - dentro do limite recomendado"
            })
    return alertas, setores

def calcular_preco_teto_bazin(ticker, dy_desejado=0.06):
    """
    Calcula preço teto pelo método Bazin.
    Retorna (preco_teto, mensagem).
    """
    try:
        if ticker[-1].isdigit():
            ticker_yf = f"{ticker}.SA"
        else:
            ticker_yf = ticker
        acao = yf.Ticker(ticker_yf)
        dividends = acao.dividends.tail(12)
        
        if dividends.empty:
            return None, "Sem histórico de dividendos"
        
        dividendo_anual_medio = dividends.mean() * 4
        preco_teto = dividendo_anual_medio / dy_desejado
        
        return preco_teto, f"R$ {preco_teto:.2f}"
    except Exception as e:
        return None, str(e)

def calcular_risco_retorno(tickers):
    """
    Calcula métricas de risco para os ativos.
    Retorna dicionário com ticker -> {retorno_medio, volatilidade, max_drawdown}.
    """
    dados_risco = {}
    for ticker in tickers:
        try:
            if ticker[-1].isdigit():
                ticker_yf = f"{ticker}.SA"
            else:
                ticker_yf = ticker
            acao = yf.Ticker(ticker_yf)
            hist = acao.history(period="1y")['Close']
            if not hist.empty:
                retornos = hist.pct_change().dropna()
                dados_risco[ticker] = {
                    'retorno_medio': retornos.mean() * 252 * 100,
                    'volatilidade': retornos.std() * np.sqrt(252) * 100,
                    'max_drawdown': (hist / hist.cummax() - 1).min() * 100
                }
        except:
            continue
    return dados_risco

def calcular_evolucao_patrimonio(df_ativos):
    """
    Calcula evolução do patrimônio nos últimos 30 dias.
    df_ativos deve ter colunas 'ticker', 'qtd'.
    Retorna DataFrame com índices das datas e coluna 'Total'.
    """
    dados_historicos = {}
    for ticker in df_ativos['ticker']:
        try:
            if ticker[-1].isdigit():
                ticker_yf = f"{ticker}.SA"
            else:
                ticker_yf = ticker
            acao = yf.Ticker(ticker_yf)
            hist = acao.history(period="1mo")
            if not hist.empty:
                qtd = df_ativos[df_ativos['ticker'] == ticker]['qtd'].iloc[0]
                dados_historicos[ticker] = hist['Close'] * qtd
        except:
            continue
    
    if dados_historicos:
        df_evolucao = pd.DataFrame(dados_historicos)
        df_evolucao['Total'] = df_evolucao.sum(axis=1)
        return df_evolucao
    return None

def calcular_rebalanceamento(df_ativos, metas, valor_disponivel=0):
    """
    Calcula quanto aportar em cada classe para atingir metas.
    df_ativos deve ter colunas 'setor' e 'Patrimônio'.
    metas: dicionário {classe: percentual_meta}
    Retorna DataFrame com recomendações.
    """
    if df_ativos.empty or not metas:
        return None
    
    total = df_ativos['Patrimônio'].sum() + valor_disponivel
    atual_por_classe = df_ativos.groupby('setor')['Patrimônio'].sum()
    
    recomendacoes = []
    for classe, meta_pct in metas.items():
        if classe not in atual_por_classe.index:
            atual = 0
            atual_pct = 0
        else:
            atual = atual_por_classe[classe]
            atual_pct = (atual / total) * 100 if total > 0 else 0
        
        alvo = total * meta_pct / 100
        diferenca = alvo - atual
        
        if diferenca > 0:
            acao = "COMPRAR"
            cor = "#00FF00"
        elif diferenca < 0:
            acao = "VENDER"
            cor = "#FF4444"
        else:
            acao = "OK"
            cor = "#D4AF37"
        
        recomendacoes.append({
            'Classe': classe,
            'Atual (R$)': atual,
            'Atual (%)': atual_pct,
            'Meta (%)': meta_pct,
            'Alvo (R$)': alvo,
            'Diferença (R$)': diferenca,
            'Ação': acao,
            'Cor': cor
        })
    
    return pd.DataFrame(recomendacoes)
