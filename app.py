import streamlit as st
import pandas as pd
import yfinance as yf
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time

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

# --- SISTEMA DE LOGIN ---
if "logado" not in st.session_state:
    st.session_state.logado = False
    st.session_state.confirmacao_exclusao = {}
    st.session_state.etapa_carteira = 1
    st.session_state.alertas = {}

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
# MENU LATERAL
# ============================================
st.sidebar.title("💎 IGORBARBO PRIVATE")
menu = st.sidebar.radio("Navegação", [
    "🏠 Dashboard", 
    "🎯 Montar Carteira",
    "📈 Evolução",
    "🔔 Alertas",
    "📝 Imposto Renda",
    "🎯 Projeção", 
    "⚙️ Gestão"
])

# ============================================
# 1. DASHBOARD
# ============================================
if menu == "🏠 Dashboard":
    st.title("🏛️ Patrimônio em Tempo Real")
    
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        st.markdown("### 📊 Resumo da Carteira")
    with col2:
        st.caption(f"🕐 {datetime.now().strftime('%H:%M:%S')}")
    with col3:
        if st.button("🔄 Atualizar Preços"):
            st.cache_data.clear()
            st.rerun()
    
    df = pd.read_sql_query("SELECT * FROM ativos", conn)
    
    if not df.empty:
        with st.spinner('🔄 Buscando preços do mercado...'):
            precos_info = []
            for ticker in df['ticker']:
                preco, status, msg = pegar_preco(ticker)
                precos_info.append({
                    'ticker': ticker,
                    'preco': preco if preco else 0,
                    'status': status,
                    'msg': msg
                })
            
            df_precos = pd.DataFrame(precos_info)
            df = df.merge(df_precos, on='ticker')
            
            df['Patrimônio'] = df['qtd'] * df['preco']
            df['Custo Total'] = df['qtd'] * df['pm']
            df['Lucro/Prejuízo'] = df['Patrimônio'] - df['Custo Total']
            df['Variação %'] = (df['preco'] / df['pm'] - 1) * 100
            
            total_patrimonio = df['Patrimônio'].sum()
            total_custo = df['Custo Total'].sum()
            total_lucro = df['Lucro/Prejuízo'].sum()
            renda_est = total_patrimonio * 0.0085
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Investido", f"R$ {total_custo:,.2f}")
        c2.metric("Patrimônio Atual", f"R$ {total_patrimonio:,.2f}")
        c3.metric("Lucro/Prejuízo", f"R$ {total_lucro:,.2f}")
        c4.metric("Renda Mensal Est.", f"R$ {renda_est:,.2f}")
        
        st.write("---")
        
        st.subheader("📋 Detalhamento por Ativo")
        
        df_display = df[['ticker', 'qtd', 'pm', 'preco', 'Patrimônio', 'Lucro/Prejuízo', 'Variação %', 'status']].copy()
        df_display.columns = ['Ticker', 'Qtd', 'P.Médio', 'P.Atual', 'Patrimônio', 'Lucro/Prej', 'Var %', 'Status']
        
        st.dataframe(
            df_display.style.format({
                'P.Médio': 'R$ {:.2f}',
                'P.Atual': 'R$ {:.2f}',
                'Patrimônio': 'R$ {:.2f}',
                'Lucro/Prej': 'R$ {:.2f}',
                'Var %': '{:.1f}%'
            }),
            use_container_width=True,
            height=400
        )
        
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.subheader("Distribuição por Ativo")
            fig1 = px.pie(df, values='Patrimônio', names='ticker', hole=0.5,
                         color_discrete_sequence=px.colors.sequential.Gold)
            st.plotly_chart(fig1, use_container_width=True)
            
        with col_g2:
            st.subheader("Distribuição por Setor")
            fig2 = px.pie(df, values='Patrimônio', names='setor', hole=0.5,
                         color_discrete_sequence=["#D4AF37", "#8B6914", "#B8860B", "#CD7F32", "#C0C0C0"])
            st.plotly_chart(fig2, use_container_width=True)
    
    else:
        st.info("📭 Sua carteira está vazia. Vá em 'Gestão de Carteira' para adicionar ativos.")
        st.info("💡 Ou use o assistente 'Montar Carteira' para começar do zero!")

# ============================================
# 2. ASSISTENTE DE CARTEIRA INTELIGENTE (CORRIGIDO)
# ============================================
elif menu == "🎯 Montar Carteira":
    st.title("🎯 Assistente Inteligente de Carteira")
    st.markdown("### Meta: Rentabilidade de **8% a 12% ao ano**")
    
    if 'etapa_carteira' not in st.session_state:
        st.session_state.etapa_carteira = 1
    
    # --- ETAPA 1: PERFIL ---
    if st.session_state.etapa_carteira == 1:
        st.markdown("---")
        st.subheader("📋 Passo 1: Conte sobre você")
        
        col1, col2 = st.columns(2)
        
        with col1:
            valor = st.number_input("💰 Quanto quer investir? (R$)", 
                                   min_value=100.0, 
                                   value=1000.0, 
                                   step=500.0,
                                   help="Valor total disponível para investir agora")
            
            perfil = st.selectbox("🎲 Seu perfil de investidor",
                                 ["Conservador", "Moderado", "Arrojado"],
                                 help="Conservador: prioriza segurança | Moderado: equilíbrio | Arrojado: busca retorno")
        
        with col2:
            prazo = st.selectbox("⏱️ Prazo do investimento",
                                ["Curto (1-2 anos)", 
                                 "Médio (3-5 anos)", 
                                 "Longo (5+ anos)"])
            
            objetivo = st.selectbox("🎯 Objetivo principal",
                                   ["Crescimento patrimonial",
                                    "Geração de renda mensal",
                                    "Proteção contra inflação"])
        
        if st.button("✅ Próximo: Ver alocação ideal", use_container_width=True):
            st.session_state.valor_investir = valor
            st.session_state.perfil_usuario = perfil
            st.session_state.prazo_usuario = prazo
            st.session_state.objetivo_usuar
