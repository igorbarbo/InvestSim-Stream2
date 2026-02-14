import streamlit as st
import pandas as pd
import yfinance as yf
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time
import numpy as np
import io

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

# --- INICIALIZAÇÃO DO SESSION STATE ---
if 'logado' not in st.session_state:
    st.session_state.logado = False
if 'confirmacao_exclusao' not in st.session_state:
    st.session_state.confirmacao_exclusao = {}
if 'etapa_carteira' not in st.session_state:
    st.session_state.etapa_carteira = 1
if 'alertas' not in st.session_state:
    st.session_state.alertas = {}
if 'metas_alocacao' not in st.session_state:
    st.session_state.metas_alocacao = carregar_metas_alocacao()
if 'valor_investir' not in st.session_state:
    st.session_state.valor_investir = 1000.0
if 'perfil_usuario' not in st.session_state:
    st.session_state.perfil_usuario = "Moderado"
if 'prazo_usuario' not in st.session_state:
    st.session_state.prazo_usuario = "Médio (3-5 anos)"
if 'objetivo_usuario' not in st.session_state:
    st.session_state.objetivo_usuario = "Crescimento patrimonial"
if 'alocacao_escolhida' not in st.session_state:
    st.session_state.alocacao_escolhida = None
if 'retorno_esperado' not in st.session_state:
    st.session_state.retorno_esperado = 0.095
if 'editando' not in st.session_state:
    st.session_state.editando = None

# --- SISTEMA DE LOGIN ---
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
# FUNÇÕES DE ANÁLISE AVANÇADA
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
        return None, None
    
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

def exportar_para_excel(df_carteira):
    """Exporta dados para Excel"""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_carteira.to_excel(writer, sheet_name='Carteira', index=False)
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
        elif diferenca < 0:
            acao = "VENDER"
        else:
            acao = "OK"
        
        recomendacoes.append({
            'Classe': classe,
            'Atual (R$)': atual,
            'Atual (%)': atual_pct,
            'Meta (%)': meta_pct,
            'Alvo (R$)': alvo,
            'Diferença (R$)': diferenca,
            'Ação': acao
        })
    
    return pd.DataFrame(recomendacoes)

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
    "📊 Análise Avançada",
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
        
        # ALERTA DE CONCENTRAÇÃO SETORIAL
        alertas_setoriais, setores = analisar_concentracao_setorial(df)
        if alertas_setoriais:
            with st.expander("⚠️ Análise de Concentração Setorial", expanded=True):
                for alerta in alertas_setoriais:
                    if alerta['nivel'] in ['CRÍTICO', 'ALTO']:
                        st.markdown(f"<p style='color:{alerta['cor']}; font-weight:bold;'>{alerta['mensagem']}</p>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<p style='color:{alerta['cor']};'>{alerta['mensagem']}</p>", unsafe_allow_html=True)
        
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
        
        # SEÇÃO DE REBALANCEAMENTO
        if st.session_state.metas_alocacao:
            st.write("---")
            st.subheader("🔄 Recomendação de Rebalanceamento")
            
            valor_aporte = st.number_input("💰 Valor disponível para aporte (R$)", 
                                          min_value=0.0, 
                                          value=0.0, 
                                          step=100.0,
                                          key="aporte_rebalanceamento")
            
            df_rebalanceamento = calcular_rebalanceamento(df, st.session_state.metas_alocacao, valor_aporte)
            
            if df_rebalanceamento is not None:
                st.dataframe(
                    df_rebalanceamento.style.format({
                        'Atual (R$)': 'R$ {:.2f}',
                        'Atual (%)': '{:.2f}%',
                        'Meta (%)': '{:.2f}%',
                        'Alvo (R$)': 'R$ {:.2f}',
                        'Diferença (R$)': 'R$ {:.2f}'
                    }),
                    use_container_width=True
                )
                
                compras = df_rebalanceamento[df_rebalanceamento['Ação'] == 'COMPRAR']
                if not compras.empty and valor_aporte > 0:
                    st.success("### 📝 Sugestão de aporte:")
                    for _, row in compras.iterrows():
                        st.write(f"• **{row['Classe']}:** aportar R$ {row['Diferença (R$)']:,.2f}")
    
    else:
        st.info("📭 Sua carteira está vazia. Vá em 'Gestão de Carteira' para adicionar ativos.")

# ============================================
# 2. ASSISTENTE DE CARTEIRA INTELIGENTE
# ============================================
elif menu == "🎯 Montar Carteira":
    st.title("🎯 Assistente Inteligente de Carteira")
    st.markdown("### Meta: Rentabilidade de **8% a 12% ao ano**")
    
    # --- ETAPA 1: PERFIL ---
    if st.session_state.etapa_carteira == 1:
        st.markdown("---")
        st.subheader("📋 Passo 1: Conte sobre você")
        
        col1, col2 = st.columns(2)
        
        with col1:
            valor = st.number_input("💰 Quanto quer investir? (R$)", 
                                   min_value=100.0, 
                                   value=st.session_state.valor_investir, 
                                   step=500.0,
                                   help="Valor total disponível para investir agora")
            
            perfil = st.selectbox("🎲 Seu perfil de investidor",
                                 ["Conservador", "Moderado", "Arrojado"],
                                 index=["Conservador", "Moderado", "Arrojado"].index(st.session_state.perfil_usuario))
        
        with col2:
            prazo = st.selectbox("⏱️ Prazo do investimento",
                                ["Curto (1-2 anos)", "Médio (3-5 anos)", "Longo (5+ anos)"],
                                index=["Curto (1-2 anos)", "Médio (3-5 anos)", "Longo (5+ anos)"].index(st.session_state.prazo_usuario))
            
            objetivo = st.selectbox("🎯 Objetivo principal",
                                   ["Crescimento patrimonial", "Geração de renda mensal", "Proteção contra inflação"],
                                   index=["Crescimento patrimonial", "Geração de renda mensal", "Proteção contra inflação"].index(st.session_state.objetivo_usuario))
        
        if st.button("✅ Próximo: Ver alocação ideal", use_container_width=True):
            st.session_state.valor_investir = valor
            st.session_state.perfil_usuario = perfil
            st.session_state.prazo_usuario = prazo
            st.session_state.objetivo_usuario = objetivo
            st.session_state.etapa_carteira = 2
            st.rerun()
    
    # --- ETAPA 2: ALOCAÇÃO ---
    elif st.session_state.etapa_carteira == 2:
        st.markdown("---")
        st.subheader("📊 Passo 2: Alocação recomendada")
        
        valor = st.session_state.valor_investir
        perfil = st.session_state.perfil_usuario
        
        if perfil == "Conservador":
            alocacao = {
                "Renda Fixa": {"pct": 70, "cor": "#2E86AB", "retorno": 0.08},
                "FIIs": {"pct": 20, "cor": "#D4AF37", "retorno": 0.09},
                "Ações": {"pct": 10, "cor": "#F18F01", "retorno": 0.10}
            }
        elif perfil == "Moderado":
            alocacao = {
                "Renda Fixa": {"pct": 40, "cor": "#2E86AB", "retorno": 0.08},
                "FIIs": {"pct": 35, "cor": "#D4AF37", "retorno": 0.10},
                "Ações": {"pct": 25, "cor": "#F18F01", "retorno": 0.12}
            }
        else:
            alocacao = {
                "Renda Fixa": {"pct": 20, "cor": "#2E86AB", "retorno": 0.08},
                "FIIs": {"pct": 40, "cor": "#D4AF37", "retorno": 0.11},
                "Ações": {"pct": 40, "cor": "#F18F01", "retorno": 0.13}
            }
        
        # Salvar metas
        metas = {classe: dados['pct'] for classe, dados in alocacao.items()}
        st.session_state.metas_alocacao = metas
        salvar_meta_alocacao(metas)
        
        df_alloc = pd.DataFrame([
            {
                "Classe": classe,
                "Percentual": f"{dados['pct']}%",
                "Valor (R$)": f"R$ {valor * dados['pct']/100:,.2f}",
                "Retorno": f"{dados['retorno']*100:.1f}%"
            }
            for classe, dados in alocacao.items()
        ])
        
        st.dataframe(df_alloc, use_container_width=True)
        
        fig = px.pie(
            values=[d['pct'] for d in alocacao.values()],
            nam
