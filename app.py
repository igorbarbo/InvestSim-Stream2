import streamlit as st
import pandas as pd
import yfinance as yf
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import numpy as np
import io
import base64

# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="Igorbarbo V8 Ultimate", layout="wide")

# Estilização Luxury
st.markdown("""
    <style>
    .stApp { background-color: #05070A; color: white; }
    [data-testid="stMetricValue"] { color: #D4AF37 !important; }
    .stProgress > div > div > div > div { background-color: #D4AF37 !important; }
    h1, h2, h3 { color: #D4AF37 !important; font-family: 'serif'; }
    .stDataFrame { background-color: #0F1116; border-radius: 10px; }
    .stButton button { background-color: #D4AF37; color: black; font-weight: bold; }
    .stButton button:hover { background-color: #B8860B; }
    .status-oportunidade { color: #00FF00; font-weight: bold; }
    .status-barato { color: #90EE90; font-weight: bold; }
    .status-atencao { color: #FFA500; font-weight: bold; }
    .status-caro { color: #FF4444; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- SISTEMA DE BANCO DE DADOS ---
def init_db():
    conn = sqlite3.connect('invest_v8.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS ativos 
                 (ticker TEXT PRIMARY KEY, qtd REAL, pm REAL, setor TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS metas_alocacao
                 (classe TEXT PRIMARY KEY, percentual REAL)''')
    conn.commit()
    return conn

conn = init_db()

def salvar_ativo(t, q, p, s):
    """Salva ativo com validações completas"""
    if not t or len(t.strip()) < 2:
        st.error("❌ Ticker inválido! Digite um ticker válido (ex: PETR4)")
        return False
    
    if q <= 0:
        st.error("❌ Quantidade deve ser maior que zero!")
        return False
    
    if p <= 0:
        st.error("❌ Preço médio deve ser maior que zero!")
        return False
    
    if not s:
        st.error("❌ Selecione um setor!")
        return False
    
    try:
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO ativos VALUES (?, ?, ?, ?)", 
                  (t.upper().strip(), float(q), float(p), s))
        conn.commit()
        st.success(f"✅ {t.upper()} salvo com sucesso!")
        time.sleep(1)
        return True
    except Exception as e:
        st.error(f"❌ Erro ao salvar: {str(e)}")
        return False

def excluir_ativo(t):
    """Exclui ativo"""
    try:
        c = conn.cursor()
        c.execute("DELETE FROM ativos WHERE ticker = ?", (t,))
        conn.commit()
        st.success(f"✅ {t} excluído!")
        time.sleep(1)
        return True
    except Exception as e:
        st.error(f"❌ Erro ao excluir: {str(e)}")
        return False

def atualizar_ativo(t, q, p, s):
    """Atualiza ativo existente"""
    try:
        c = conn.cursor()
        c.execute("UPDATE ativos SET qtd=?, pm=?, setor=? WHERE ticker=?", 
                  (float(q), float(p), s, t.upper().strip()))
        conn.commit()
        st.success(f"✅ {t.upper()} atualizado com sucesso!")
        time.sleep(1)
        return True
    except Exception as e:
        st.error(f"❌ Erro ao atualizar: {str(e)}")
        return False

def salvar_meta_alocacao(metas):
    """Salva metas de alocação no banco"""
    try:
        c = conn.cursor()
        c.execute("DELETE FROM metas_alocacao")
        for classe, percentual in metas.items():
            c.execute("INSERT INTO metas_alocacao VALUES (?, ?)", (classe, percentual))
        conn.commit()
        return True
    except Exception as e:
        st.error(f"❌ Erro ao salvar metas: {str(e)}")
        return False

def carregar_metas_alocacao():
    """Carrega metas de alocação do banco"""
    try:
        c = conn.cursor()
        c.execute("SELECT classe, percentual FROM metas_alocacao")
        resultados = c.fetchall()
        return {classe: percentual for classe, percentual in resultados}
    except:
        return {}

# --- SISTEMA DE LOGIN ---
if "logado" not in st.session_state:
    st.session_state.logado = False
    st.session_state.confirmacao_exclusao = {}
    st.session_state.etapa_carteira = 1
    st.session_state.alertas = {}
    st.session_state.metas_alocacao = carregar_metas_alocacao()

if not st.session_state.logado:
    st.title("🏛️ Acesso Restrito")
    senha = st.text_input("Digite a senha para acessar seu Private Banking:", type="password")
    if st.button("Entrar"):
        if senha == "1234":
            st.session_state.logado = True
            st.rerun()
        else:
            st.error("Senha Incorreta")
    st.stop()

# --- LOGICA DE PREÇOS BÁSICA ---
@st.cache_data(ttl=300)
def pegar_preco(ticker):
    """Busca preço atual do ativo"""
    try:
        acao = yf.Ticker(f"{ticker}.SA")
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

# ============================================
# FUNÇÕES DE ANÁLISE INTELIGENTE
# ============================================

@st.cache_data(ttl=3600)
def buscar_dados_historicos(ticker, periodo="5y"):
    """Busca dados históricos do ativo para análise"""
    try:
        acao = yf.Ticker(f"{ticker}.SA")
        hist = acao.history(period=periodo)
        
        if hist.empty:
            return None
        
        preco_atual = hist['Close'].iloc[-1]
        preco_medio_12m = hist['Close'].tail(252).mean()
        preco_medio_5y = hist['Close'].mean()
        
        percentil_20 = hist['Close'].quantile(0.20)
        percentil_80 = hist['Close'].quantile(0.80)
        
        minimo_5y = hist['Close'].min()
        maximo_5y = hist['Close'].max()
        
        if len(hist) > 252:
            preco_1ano_atras = hist['Close'].iloc[-252] if len(hist) >= 252 else hist['Close'].iloc[0]
            variacao_anual = (preco_atual / preco_1ano_atras - 1) * 100
        else:
            variacao_anual = 0
        
        try:
            dividendos = acao.dividends.tail(12).mean() * 4
            if dividendos > 0 and preco_atual > 0:
                dy = (dividendos / preco_atual) * 100
            else:
                dy = None
        except:
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
    Analisa se o preço atual está caro ou barato baseado em dados históricos
    """
    if not dados_historicos:
        return "neutro", "🔵 DADOS INSUFICIENTES", "#808080", "Não foi possível buscar dados históricos para análise", 0
    
    preco = dados_historicos['preco_atual']
    media_12m = dados_historicos['preco_medio_12m']
    p20 = dados_historicos['percentil_20']
    p80 = dados_historicos['percentil_80']
    minimo = dados_historicos['minimo_5y']
    maximo = dados_historicos['maximo_5y']
    
    posicao_relativa = ((preco - minimo) / (maximo - minimo)) * 100 if maximo > minimo else 50
    
    pontuacao = 0
    motivos = []
    
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
    
    if preco < p20:
        pontuacao -= 30
        motivos.append("💰 Entre os 20% preços mais baixos dos últimos 5 anos")
    elif preco > p80:
        pontuacao += 30
        motivos.append("⚠️ Entre os 20% preços mais altos dos últimos 5 anos")
    
    if posicao_relativa < 15:
        pontuacao -= 25
        motivos.append(f"🎯 Próximo da mínima histórica (R$ {minimo:.2f})")
    elif posicao_relativa < 30:
        pontuacao -= 15
        motivos.append(f"📊 Na faixa inferior da série histórica")
    elif posicao_relativa > 85:
        pontuacao += 25
        motivos.append(f"🔴 Próximo da máxima histórica (R$ {maximo:.2f})")
    elif posicao_relativa > 70:
        pontuacao += 15
        motivos.append(f"📊 Na faixa superior da série histórica")
    
    if dados_historicos['variacao_anual'] < -20:
        pontuacao -= 20
        motivos.append(f"📉 Caiu {dados_historicos['variacao_anual']:.1f}% no último ano")
    elif dados_historicos['variacao_anual'] < -10:
        pontuacao -= 10
        motivos.append(f"📉 Caiu {dados_historicos['variacao_anual']:.1f}% no último ano")
    elif dados_historicos['variacao_anual'] > 50:
        pontuacao += 25
        motivos.append(f"🚀 Subiu {dados_historicos['variacao_anual']:.1f}% no último ano")
    elif dados_historicos['variacao_anual'] > 30:
        pontuacao += 15
        motivos.append(f"🚀 Subiu {dados_historicos['variacao_anual']:.1f}% no último ano")
    
    if pontuacao <= -40:
        status = "oportunidade"
        mensagem = "🔥 OPORTUNIDADE! Muito barato"
        cor = "#00FF00"
        emoji = "🟢"
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
    
    elif pontuacao <= -20:
        status = "barato"
        mensagem = "👍 Barato - Bom momento"
        cor = "#90EE90"
        emoji = "🟢"
        explicacao = "### ✅ PREÇO ATRATIVO\n\n"
        explicacao += "**Este ativo está abaixo da média histórica:**\n\n"
        for m in motivos[:3]:
            explicacao += f"• {m}\n"
        explicacao += f"\n📊 **Preço atual:** R$ {preco:.2f}\n"
        explicacao += f"📊 **Média 12m:** R$ {media_12m:.2f}\n"
        if dados_historicos['dividend_yield']:
            explicacao += f"💰 **Dividend Yield:** {dados_historicos['dividend_yield']:.2f}%\n"
        explicacao += f"\n💡 **RECOMENDAÇÃO:** Pode comprar - preço justo"
    
    elif pontuacao <= 0:
        status = "neutro"
        mensagem = "⚖️ Preço justo"
        cor = "#D4AF37"
        emoji = "🟡"
        explicacao = "### ⚖️ PREÇO JUSTO\n\n"
        explicacao += "**Este ativo está dentro da faixa histórica normal:**\n\n"
        for m in motivos[:2]:
            explicacao += f"• {m}\n"
        explicacao += f"\n📊 **Preço atual:** R$ {preco:.2f}\n"
        explicacao += f"📊 **Média 12m:** R$ {media_12m:.2f}\n"
        explicacao += f"\n💡 **RECOMENDAÇÃO:** Compra neutra - nem barato nem caro"
    
    elif pontuacao <= 20:
        status = "atencao"
        mensagem = "⚠️ Atenção - Acima da média"
        cor = "#FFA500"
        emoji = "🟠"
        explicacao = "### ⚠️ PREÇO ELEVADO\n\n"
        explicacao += "**Este ativo está acima da média histórica:**\n\n"
        for m in motivos[:3]:
            explicacao += f"• {m}\n"
        explicacao += f"\n📊 **Preço atual:** R$ {preco:.2f}\n"
        explicacao += f"📊 **Média 12m:** R$ {media_12m:.2f}\n"
        explicacao += f"📊 **Máxima 5 anos:** R$ {maximo:.2f}\n"
        explicacao += f"\n💡 **RECOMENDAÇÃO:** Comprar só se necessário - preço salgado"
    
    else:
        status = "caro"
        mensagem = "❌ CARO! Evite comprar"
        cor = "#FF4444"
        emoji = "🔴"
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
    
    return status, mensagem, cor, explicacao, pontuacao

def plotar_grafico_historico(dados_historicos, ticker):
    """Gera gráfico com análise de preço"""
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
        name="Faixa Normal"
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
# NOVAS FUNÇÕES: CORRELAÇÃO, PREÇO TETO, EXPORTAÇÃO, REBALANCEAMENTO
# ============================================

def calcular_matriz_correlacao(tickers, periodo="1y"):
    """Calcula matriz de correlação entre os ativos"""
    if len(tickers) < 2:
        return None, None
    
    dados = {}
    for ticker in tickers:
        try:
            acao = yf.Ticker(f"{ticker}.SA")
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
    """Analisa concentração por setor e emite alertas"""
    if df_ativos.empty:
        return None
    
    total = df_ativos['Patrimônio'].sum()
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
    Calcula preço teto pelo método Bazin
    Preço teto = (Dividendo anual médio) / (DY desejado)
    """
    try:
        acao = yf.Ticker(f"{ticker}.SA")
        dividends = acao.dividends.tail(12)
        
        if dividends.empty:
            return None, "Sem histórico de dividendos"
        
        dividendo_anual_medio = dividends.mean() * 4
        preco_teto = dividendo_anual_medio / dy_desejado
        
        return preco_teto, f"R$ {preco_teto:.2f}"
    except Exception as e:
        return None, str(e)

def calcular_preco_teto_graham(ticker, lpa, vpa):
    """
    Calcula preço teto pelo método de Graham
    Preço justo = √(22.5 * LPA * VPA)
    """
    try:
        preco_justo = np.sqrt(22.5 * lpa * vpa)
        return preco_justo
    except:
        return None

def exportar_para_excel(df_carteira, df_analise=None):
    """Exporta dados para Excel"""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_carteira.to_excel(writer, sheet_name='Carteira', index=False)
        if df_analise is not None:
            df_analise.to_excel(writer, sheet_name='Análise', index=False)
    output.seek(0)
    return output

def exportar_para_csv(df):
    """Exporta dados para CSV"""
    return df.to_csv(index=False).encode('utf-8')

def calcular_rebalanceamento(df_ativos, metas, valor_disponivel=0):
    """
    Calcula quanto aportar em cada classe para atingir metas
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

# ============================================
# MENU LATERAL
# ========
