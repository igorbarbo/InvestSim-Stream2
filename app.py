import streamlit as st
import pandas as pd
import yfinance as yf
import sqlite3
import plotly.express as px
from datetime import datetime
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

# --- LOGICA DE PREÇOS ---
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

# --- MENU LATERAL ---
st.sidebar.title("💎 IGORBARBO PRIVATE")
menu = st.sidebar.radio("Navegação", ["🏠 Dashboard", "💡 Sugestão de Aporte", "🎯 Projeção & Disciplina", "⚙️ Gestão de Carteira"])

# --- 1. DASHBOARD ---
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

# --- 2. SUGESTÃO DE APORTE ---
elif menu == "💡 Sugestão de Aporte":
    st.title("🎯 Onde investir meus R$ 150?")
    
    valor = st.number_input("💰 Valor disponível hoje (R$)", min_value=0.0, value=150.0, step=10.0)
    
    sugestoes = [
        {"Ativo": "MXRF11", "Tipo": "FII Papel", "Preço": 10.50, "Yield": "1.02%", "Recomendação": "COMPRA"},
        {"Ativo": "GALG11", "Tipo": "FII Logística", "Preço": 9.20, "Yield": "0.91%", "Recomendação": "COMPRA"},
        {"Ativo": "CPTS11", "Tipo": "FII Papel", "Preço": 8.60, "Yield": "0.88%", "Recomendação": "NEUTRA"},
        {"Ativo": "KNRI11", "Tipo": "FII Tijolo", "Preço": 120.50, "Yield": "0.65%", "Recomendação": "MANTER"},
        {"Ativo": "CDB 110%", "Tipo": "Renda Fixa", "Preço": 100.00, "Yield": "0.85%", "Recomendação": "COMPRA"}
    ]
    
    df_s = pd.DataFrame(sugestoes)
    df_s['Cotas Possíveis'] = (valor // df_s['Preço']).astype(int)
    df_s['Investimento'] = df_s['Cotas Possíveis'] * df_s['Preço']
    df_s['Troco'] = valor - df_s['Investimento']
    
    st.write(f"### Recomendações para R$ {valor:.2f}")
    
    st.dataframe(
        df_s.style.format({
            'Preço': 'R$ {:.2f}',
            'Investimento': 'R$ {:.2f}',
            'Troco': 'R$ {:.2f}'
        }),
        use_container_width=True
    )
    
    col_estr1, col_estr2 = st.columns(2)
    
    with col_estr1:
        st.info("""
        ### 💡 Estratégia Base 10
        Ativos com preço próximo de R$ 10 são ideais para aportes de R$ 150.
        """)
    
    with col_estr2:
        st.write("### 🧮 Simulador Rápido")
        ativo_escolhido = st.selectbox("Escolha um ativo:", df_s['Ativo'].tolist())
        ativo_info = df_s[df_s['Ativo'] == ativo_escolhido].iloc[0]
        
        cotas = int(valor // ativo_info['Preço'])
        investido = cotas * ativo_info['Preço']
        troco = valor - investido
        
        st.metric("Cotas que comprará", cotas)
        st.metric("Total investido", f"R$ {investido:.2f}")
        st.metric("Troco", f"R$ {troco:.2f}")

# --- 3. PROJEÇÃO & DISCIPLINA ---
elif menu == "🎯 Projeção & Disciplina":
    st.title("🚀 O Poder do Reinvestimento")
    
    col1, col2 = st.columns(2)
    
    with col1:
        aporte = st.number_input("💰 Aporte Mensal (R$)", value=150.0, step=50.0)
        taxa_anual = st.slider("📈 Rentabilidade Anual Estimada (%)", 5, 20, 10) / 100
        taxa_mensal = (1 + taxa_anual) ** (1/12) - 1
    
    with col2:
        anos = st.slider("⏳ Período (anos)", 1, 40, 10)
        meses = anos * 12
    
    df_p = pd.DataFrame({'Mês': range(1, meses+1)})
    df_p['Com Reinvestimento'] = [aporte * (((1+taxa_mensal)**m - 1)/taxa_mensal) for m in df_p['Mês']]
    df_p['Sem Reinvestimento'] = [aporte * m for m in df_p['Mês']]
    
    final_com = df_p['Com Reinvestimento'].iloc[-1]
    final_sem = df_p['Sem Reinvestimento'].iloc[-1]
    diferenca = final_com - final_sem
    
    col_m1, col_m2, col_m3 = st.columns(3)
    col_m1.metric("Total Aportado", f"R$ {aporte * meses:,.2f}")
    col_m2.metric("Com Reinvestimento", f"R$ {final_com:,.2f}")
    col_m3.metric("Sem Reinvestimento", f"R$ {final_sem:,.2f}")
    
    fig = px.line(df_p, x='Mês', y=['Com Reinvestimento', 'Sem Reinvestimento'],
                  title=f"Projeção para {anos} anos",
                  color_discrete_map={'Com Reinvestimento': '#D4AF37', 'Sem Reinvestimento': '#FF4B4B'})
    st.plotly_chart(fig, use_container_width=True)
    
    st.error(f"""
    ### ⚠️ ATENÇÃO: Custo de não reinvestir
    
    Se você gastar os rendimentos, **deixará de ganhar R$ {diferenca:,.2f}** em {anos} anos.
    """)

# --- 4. GESTÃO DE CARTEIRA ---
elif menu == "⚙️ Gestão de Carteira":
    st.title("⚙️ Gerenciar Ativos")
    
    tab1, tab2 = st.tabs(["📥 Adicionar", "✏️ Editar/Excluir"])
    
    with tab1:
        with st.form("add_ativo", clear_on_submit=True):
            st.subheader("➕ Novo Ativo")
            
            col1, col2 = st.columns(2)
            
            with col1:
                ticker = st.text_input("📌 Ticker", help="Ex: PETR4, MXRF11").upper()
                qtd = st.number_input("🔢 Quantidade", min_value=0.01, step=0.01, format="%.2f")
            
            with col2:
                pm = st.number_input("💵 Preço Médio (R$)", min_value=0.01, step=0.01, format="%.2f")
                setor = st.selectbox("🏷️ Setor", 
                                    ["Ações", "FII Papel", "FII Tijolo", "ETF", "Renda Fixa"])
            
            submitted = st.form_submit_button("💾 Salvar Ativo", use_container_width=True)
            if submitted:
                if salvar_ativo(ticker, qtd, pm, setor):
                    st.balloons()
    
    with tab2:
        st.subheader("📋 Ativos Cadastrados")
        
        df_lista = pd.read_sql_query("SELECT * FROM ativos ORDER BY ticker", conn)
        
        if not df_lista.empty:
            if 'editando' not in st.session_state:
                st.session_state.editando = None
            if 'excluindo' not in st.session_state:
                st.session_state.excluindo = None
            
            for idx, row in df_lista.iterrows():
                with st.container():
                    col1, col2, col3 = st.columns([4, 1, 1])
                    
                    with col1:
                        st.write(f"**{row['ticker']}** | {row['qtd']:.2f} cotas | R$ {row['pm']:.2f} | {row['setor']}")
                    
                    with col2:
                        if st.button(f"✏️", key=f"edit_{row['ticker']}", use_container_width=True):
                            st.session_state.editando = row['ticker']
                            st.session_state.edit_qtd = row['qtd']
                            st.session_state.edit_pm = row['pm']
                            st.session_state.edit_setor = row['setor']
                            st.rerun()
                    
                    with col3:
                        if st.button(f"🗑️", key=f"del_{row['ticker']}", use_container_width=True):
                            st.session_state.excluindo = row['ticker']
                            st.rerun()
                    
                    if st.session_state.editando == row['ticker']:
                        with st.form(key=f"form_edit_{row['ticker']}"):
                            st.write(f"**Editando: {row['ticker']}**")
                            
                            col_e1, col_e2, col_e3 = st.columns(3)
                            with col_e1:
                                nova_qtd = st.number_input("Quantidade", value=float(st.session_state.edit_qtd), min_value=0.01)
                            with col_e2:
                                novo_pm = st.number_input("Preço Médio", value=float(st.session_state.edit_pm), min_value=0.01)
                            with col_e3:
                                novo_setor = st.selectbox("Setor", 
                                                         ["Ações", "FII Papel", "FII Tijolo", "ETF", "Renda Fixa"],
                                                         index=["Ações", "FII Papel", "FII Tijolo", "ETF", "Renda Fixa"].index(st.session_state.edit_setor))
                            
                            col_b1, col_b2 = st.columns(2)
                            with col_b1:
                                if st.form_submit_button("💾 Salvar", use_container_width=True):
                                    if atualizar_ativo(row['ticker'], nova_qtd, novo_pm, novo_setor):
                                        st.session_state.editando = None
                                        st.rerun()
                            with col_b2:
                                if st.form_submit_button("❌ Cancelar", use_container_width=True):
                                    st.session_state.editando = None
                                    st.rerun()
                    
                    if st.session_state.excluindo == row['ticker']:
                        st.warning(f"Tem certeza que deseja excluir **{row['ticker']}**?")
                        col_c1, col_c2 = st.columns(2)
                        with col_c1:
                            if st.button(f"✅ Sim", key=f"confirm_yes_{row['ticker']}", use_container_width=True):
                                if excluir_ativo(row['ticker']):
                                    st.session_state.excluindo = None
                                    st.rerun()
                        with col_c2:
                            if st.button(f"❌ Não", key=f"confirm_no_{row['ticker']}", use_container_width=True):
                                st.session_state.excluindo = None
                                st.rerun()
                    
                    st.divider()
        else:
            st.info("📭 Nenhum ativo cadastrado.")

# --- RODAPÉ ---
st.sidebar.markdown("---")
st.sidebar.caption(f"🕐 Último acesso: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
st.sidebar.caption("💎 Igorbarbo Private Banking v8.0")
