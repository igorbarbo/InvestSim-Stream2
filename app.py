import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import time
import numpy as np

# Importações dos módulos personalizados
from Modules import (
    salvar_ativo, excluir_ativo, atualizar_ativo, carregar_ativos,
    salvar_metas, carregar_metas,
    salvar_alerta, carregar_alertas, excluir_alerta,
    pegar_preco, pegar_preco_simples,
    buscar_dados_historicos, analisar_preco_ativo, plotar_grafico_historico,
    calcular_matriz_correlacao, analisar_concentracao_setorial,
    calcular_preco_teto_bazin, calcular_risco_retorno, calcular_evolucao_patrimonio,
    exportar_para_excel, exportar_para_csv,
    ATIVOS,
    criar_authenticator, buscar_usuario_por_username,
    init_db, get_connection
)

# ============================================
# INICIALIZAÇÃO DO BANCO DE DADOS
# ============================================
init_db()
conn = get_connection()# ============================================
# SISTEMA DE LOGIN (AUTENTICAÇÃO REAL)
# ============================================
authenticator = criar_authenticator()
authenticator.login()

if st.session_state["authentication_status"]:
    username = st.session_state["username"]
    name = st.session_state["name"]
    user_info = buscar_usuario_por_username(username)
    if user_info:
        user_id = user_info['id']
        st.session_state.user_id = user_id
        st.session_state.username = username
        st.session_state.name = name
    else:
        st.error("Usuário não encontrado no banco.")
        st.stop()

    authenticator.logout('Sair', 'sidebar')
    st.sidebar.success(f'Bem-vindo, {name}!')

elif st.session_state["authentication_status"] == False:
    st.error('Usuário ou senha incorretos')
    st.stop()
else:
    st.warning('Por favor, faça o login')
    st.stop()# ============================================
# MENU LATERAL
# ============================================
st.sidebar.title("💎 IGORBARBO PRIVATE")
menu = st.sidebar.radio("Navegação", [
    "🏠 Dashboard",
    "🎯 Montar Carteira",
    "📈 Evolução",
    "🔔 Alertas",
    "📝 Imposto Renda",
    "💰 Preço Teto",
    "📊 Análise Avançada",
    "⚙️ Gestão"
])# ============================================
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
    
    df = carregar_ativos(st.session_state.user_id)
    
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
        
        # Alertas setoriais
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
        
        # Seção de rebalanceamento
        metas = carregar_metas(st.session_state.user_id)
        if metas:
            st.write("---")
            st.subheader("🔄 Recomendação de Rebalanceamento")
            
            valor_aporte = st.number_input("💰 Valor disponível para aporte (R$)", 
                                          min_value=0.0, 
                                          value=0.0, 
                                          step=100.0,
                                          key="aporte_rebalanceamento")
            
            from Modules.analise import calcular_rebalanceamento
            df_rebalanceamento = calcular_rebalanceamento(df, metas, valor_aporte)
            
            if df_rebalanceamento is not None:
                st.dataframe(
                    df_rebalanceamento.style.format({
                        'Atual (R$)': 'R$ {:.2f}',
                        'Atual (%)': '{:.2f}%',
                        'Meta (%)': '{:.2f}%',
                        'Alvo (R$)': 'R$ {:.2f}',
                        'Diferença (R$)': 'R$ {:.2f}'
                    }).applymap(lambda x: f'color: {x}' if isinstance(x, str) and x in ['COMPRAR', 'VENDER', 'OK'] else '', subset=['Ação']),
                    use_container_width=True
                )
                
                compras = df_rebalanceamento[df_rebalanceamento['Ação'] == 'COMPRAR']
                if not compras.empty and valor_aporte > 0:
                    st.success("### 📝 Sugestão de aporte:")
                    for _, row in compras.iterrows():
                        st.write(f"• **{row['Classe']}:** aportar R$ {row['Diferença (R$)']:,.2f} para atingir a meta")
    else:
        st.info("📭 Sua carteira está vazia. Vá em 'Gestão de Carteira' para adicionar ativos.")
        st.info("💡 Ou use o assistente 'Montar Carteira' para começar do zero!")# ============================================
# 2. ASSISTENTE DE CARTEIRA INTELIGENTE
# ============================================
# ============================================
# 2. ASSISTENTE DE CARTEIRA INTELIGENTE
# ============================================
elif menu == "🎯 Montar Carteira":
    st.title("🎯 Assistente Inteligente de Carteira")
    st.markdown("### Meta: Rentabilidade de **8% a 12% ao ano**")
    
    if 'etapa_carteira' not in st.session_state:
        st.session_state.etapa_carteira = 1
        st.session_state.valor_investir = 1000.0
        st.session_state.perfil_usuario = "Moderado"
        st.session_state.prazo_usuario = "Médio (3-5 anos)"
        st.session_state.objetivo_usuario = "Crescimento patrimonial"
        st.session_state.alocacao_escolhida = None
        st.session_state.retorno_esperado = 0.095
    
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
                                 index=["Conservador", "Moderado", "Arrojado"].index(st.session_state.perfil_usuario),
                                 help="Conservador: prioriza segurança | Moderado: equilíbrio | Arrojado: busca retorno")
        
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
        st.subheader("📊 Passo 2: Alocação recomendada para seu perfil")
        
        valor = st.session_state.valor_investir
        perfil = st.session_state.perfil_usuario
        
        if perfil == "Conservador":
            alocacao = {
                "Renda Fixa": {"pct": 70, "cor": "#2E86AB", "retorno": 0.08},
                "FIIs": {"pct": 20, "cor": "#D4AF37", "retorno": 0.09},
                "Ações": {"pct": 10, "cor": "#F18F01", "retorno": 0.10}
            }
            descricao = "🔒 Foco em segurança, com pequena exposição a risco"
            
        elif perfil == "Moderado":
            alocacao = {
                "Renda Fixa": {"pct": 40, "cor": "#2E86AB", "retorno": 0.08},
                "FIIs": {"pct": 35, "cor": "#D4AF37", "retorno": 0.10},
                "Ações": {"pct": 25, "cor": "#F18F01", "retorno": 0.12}
            }
            descricao = "⚖️ Equilíbrio entre segurança e rentabilidade"
            
        else:  # Arrojado
            alocacao = {
                "Renda Fixa": {"pct": 20, "cor": "#2E86AB", "retorno": 0.08},
                "FIIs": {"pct": 40, "cor": "#D4AF37", "retorno": 0.11},
                "Ações": {"pct": 40, "cor": "#F18F01", "retorno": 0.13}
            }
            descricao = "🚀 Busca pelo máximo retorno, assumindo riscos"
        
        st.info(f"📌 **Seu perfil:** {perfil} - {descricao}")
        
        # Salvar metas para rebalanceamento
        metas = {classe: dados['pct'] for classe, dados in alocacao.items()}
        salvar_metas(st.session_state.user_id, metas)
        
        df_alloc = pd.DataFrame([
            {
                "Classe": classe,
                "Percentual": f"{dados['pct']}%",
                "Valor (R$)": f"R$ {valor * dados['pct']/100:,.2f}",
                "Retorno Anual": f"{dados['retorno']*100:.1f}%"
            }
            for classe, dados in alocacao.items()
        ])
        
        st.dataframe(df_alloc, use_container_width=True)
        
        fig = px.pie(
            values=[d['pct'] for d in alocacao.values()],
            names=list(alocacao.keys()),
            title="Distribuição da Carteira",
            color_discrete_sequence=[d['cor'] for d in alocacao.values()]
        )
        st.plotly_chart(fig, use_container_width=True)
        
        retorno_total = sum((d['pct']/100) * d['retorno'] for d in alocacao.values())
        
        col_r1, col_r2, col_r3 = st.columns(3)
        with col_r1:
            st.metric("Total a Investir", f"R$ {valor:,.2f}")
        with col_r2:
            st.metric("Retorno Anual Esperado", f"{retorno_total*100:.1f}%")
        with col_r3:
            renda_mensal = valor * retorno_total / 12
            st.metric("Renda Mensal Estimada", f"R$ {renda_mensal:,.2f}")
        
        if 0.08 <= retorno_total <= 0.12:
            st.success("✅ Esta carteira está dentro da meta de 8% a 12% ao ano!")
        elif retorno_total < 0.08:
            st.warning("⚠️ Esta carteira está abaixo da meta de 8%. Considere um perfil mais arrojado.")
        else:
            st.warning("⚠️ Esta carteira está acima da meta de 12%. Considere um perfil mais conservador.")
        
        col_b1, col_b2 = st.columns(2)
        with col_b1:
            if st.button("🔙 Voltar ao perfil", use_container_width=True):
                st.session_state.etapa_carteira = 1
                st.rerun()
        with col_b2:
            if st.button("✅ Aceitar e escolher ativos", use_container_width=True):
                st.session_state.alocacao_escolhida = alocacao
                st.session_state.retorno_esperado = retorno_total
                st.session_state.etapa_carteira = 3
                st.rerun()("📈 Passo 3: Escolha seus ativos com análise inteligente")
    
    valor = st.session_state.valor_investir
    alocacao = st.session_state.alocacao_escolhida
    
    from Modules.config import ATIVOS
    carteira_montada = []
    
    for classe, dados in alocacao.items():
        valor_classe = valor * dados['pct']/100
        
        with st.expander(f"### 📌 {classe} - R$ {valor_classe:,.2f} ({dados['pct']}%)", expanded=True):
            st.caption(f"Retorno esperado para esta classe: {dados['retorno']*100:.1f}% a.a.")
            
            if classe in ATIVOS:
                for ativo in ATIVOS[classe]:
                    with st.container():
                        with st.spinner(f"Analisando {ativo['ticker']}..."):
                            dados_hist = buscar_dados_historicos(ativo['ticker'])
                            status, msg_status, cor_status, explicacao, pontuacao = analisar_preco_ativo(ativo['ticker'], dados_hist)
                        
                        col1, col2, col3, col4, col5, col6 = st.columns([1.2, 2, 1, 1, 1.5, 1.2])
                        
                        with col1:
                            st.write(f"**{ativo['ticker']}**")
                        
                        with col2:
                            st.write(ativo['nome'][:20] + "...")
                        
                        with col3:
                            st.write(f"R$ {ativo['preco']:.2f}")
                        
                        with col4:
                            if status == "neutro" and msg_status == "🔵 DADOS INSUFICIENTES":
                                st.markdown(f"<span style='color:{cor_status}' title='Ativos de renda fixa não possuem histórico de preços para análise comparativa.'>🔵 DADOS INSUF.</span>", unsafe_allow_html=True)
                            else:
                                st.markdown(f"<span style='color:{cor_status}'>{msg_status[:10]}...</span>", unsafe_allow_html=True)
                        
                        with col5:
                            cotas_max = int(valor_classe // ativo['preco'])
                            if cotas_max > 0:
                                cotas = st.number_input("Qtd", 
                                                       min_value=0, 
                                                       max_value=cotas_max,
                                                       value=0,
                                                       step=1,
                                                       key=f"qtd_{classe}_{ativo['ticker']}",
                                                       label_visibility="collapsed")
                            else:
                                cotas = 0
                                st.write("💰")
                        
                        with col6:
                            if st.button("🔍", key=f"info_{ativo['ticker']}", help="Ver análise detalhada"):
                                st.session_state[f"show_info_{ativo['ticker']}"] = not st.session_state.get(f"show_info_{ativo['ticker']}", False)
                        
                        if st.session_state.get(f"show_info_{ativo['ticker']}", False):
                            with st.container():
                                st.markdown(f"<div style='background-color: #1A1A1A; padding: 10px; border-radius: 5px; margin: 5px 0;'>", unsafe_allow_html=True)
                                st.markdown(explicacao)
                                
                                if dados_hist:
                                    fig = plotar_grafico_historico(dados_hist, ativo['ticker'])
                                    if fig:
                                        st.plotly_chart(fig, use_container_width=True)
                                
                                if st.button("Ocultar", key=f"hide_{ativo['ticker']}"):
                                    st.session_state[f"show_info_{ativo['ticker']}"] = False
                                    st.rerun()
                                st.markdown("</div>", unsafe_allow_html=True)
                        
                        if cotas > 0:
                            investimento = cotas * ativo['preco']
                            if investimento <= valor_classe:
                                carteira_montada.append({
                                    "Classe": classe,
                                    "Ticker": ativo['ticker'],
                                    "Nome": ativo['nome'],
                                    "Preço": ativo['preco'],
                                    "Cotas": cotas,
                                    "Investimento": investimento,
                                    "Status": status,
                                    "Pontuação": pontuacao
                                })
                        
                        st.divider()
    
    if carteira_montada:
        st.markdown("---")
        st.success("### 🎯 Sua carteira montada!")
        
        df_final = pd.DataFrame(carteira_montada)
        total_investido = df_final['Investimento'].sum()
        sobra = valor - total_investido
        
        df_resumo = df_final.groupby('Classe').agg({
            'Investimento': 'sum',
            'Ticker': 'count'
        }).reset_index()
        df_resumo.columns = ['Classe', 'Investido', 'Qtd Ativos']
        
        col_r1, col_r2 = st.columns(2)
        
        with col_r1:
            st.subheader("📊 Resumo por Classe")
            for _, row in df_resumo.iterrows():
                pct_real = (row['Investido'] / valor) * 100
                st.write(f"**{row['Classe']}:** R$ {row['Investido']:,.2f} ({pct_real:.1f}%) - {row['Qtd Ativos']} ativos")
        
        with col_r2:
            st.subheader("📈 Retorno Estimado")
            st.metric("Retorno Anual", f"{st.session_state.retorno_esperado*100:.1f}%")
            renda_mensal = total_investido * st.session_state.retorno_esperado / 12
            st.metric("Renda Mensal", f"R$ {renda_mensal:,.2f}")
        
        st.subheader("📋 Ativos Selecionados")
        
        df_display = df_final[['Ticker', 'Nome', 'Preço', 'Cotas', 'Investimento', 'Status']].copy()
        
        def colorir_status(val):
            if val == 'oportunidade':
                return 'background-color: #006400'
            elif val == 'barato':
                return 'background-color: #006400'
            elif val == 'neutro':
                return 'background-color: #8B6914'
            elif val == 'atencao':
                return 'background-color: #8B4500'
            elif val == 'caro':
                return 'background-color: #8B0000'
            return ''
        
        st.dataframe(
            df_display.style.format({
                'Preço': 'R$ {:.2f}',
                'Investimento': 'R$ {:.2f}'
            }).applymap(colorir_status, subset=['Status']),
            use_container_width=True
        )
        
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            st.metric("Total investido", f"R$ {total_investido:,.2f}")
        with col_f2:
            st.metric("Sobra", f"R$ {sobra:,.2f}")
        with col_f3:
            st.metric("Cotas totais", df_final['Cotas'].sum())
        
        if sobra > 0:
            st.info(f"💡 Com R$ {sobra:.2f} de sobra, você pode aumentar posições existentes ou guardar para o próximo aporte")
        
        col_b1, col_b2, col_b3 = st.columns(3)
        with col_b1:
            if st.button("🔄 Recomeçar", use_container_width=True):
                st.session_state.etapa_carteira = 1
                st.rerun()
        with col_b2:
            if st.button("💾 Salvar na Carteira", use_container_width=True):
                for _, ativo in df_final.iterrows():
                    salvar_ativo(
                        st.session_state.user_id,
                        ativo['Ticker'], 
                        ativo['Cotas'], 
                        ativo['Preço'], 
                        ativo['Classe']
                    )
                st.balloons()
                st.success("✅ Todos os ativos foram salvos na sua carteira!")
                st.info("📋 Vá para o Dashboard para acompanhar seus investimentos")# ============================================
# 3. EVOLUÇÃO
# ============================================
elif menu == "📈 Evolução":
    st.title("📈 Evolução do Patrimônio")
    
    df = carregar_ativos(st.session_state.user_id)
    
    if df.empty:
        st.info("Adicione ativos para ver a evolução")
    else:
        with st.spinner("Buscando dados históricos..."):
            df_evolucao = calcular_evolucao_patrimonio(df)
            
            if df_evolucao is not None:
                fig = px.line(df_evolucao, y='Total', 
                             title="Patrimônio Total - Últimos 30 Dias",
                             labels={'value': 'Patrimônio (R$)', 'index': 'Data'})
                fig.update_traces(line_color='#D4AF37', line_width=3)
                st.plotly_chart(fig, use_container_width=True)
                
                col_ev1, col_ev2, col_ev3 = st.columns(3)
                with col_ev1:
                    variacao = (df_evolucao['Total'].iloc[-1] / df_evolucao['Total'].iloc[0] - 1) * 100
                    st.metric("Variação no Período", f"{variacao:.2f}%")
                with col_ev2:
                    st.metric("Máximo", f"R$ {df_evolucao['Total'].max():,.2f}")
                with col_ev3:
                    st.metric("Mínimo", f"R$ {df_evolucao['Total'].min():,.2f}")
            else:
                st.warning("Não foi possível buscar dados históricos")
        with col_b3:
            if st.button("📊 Ver Dashboard", use_container_width=True):
                st.session_state.etapa_carteira = 1
                st.rerun()
    else:
        st.info("👆 Selecione as quantidades de cada ativo para montar sua carteira")# ============================================
# 4. ALERTAS
# ============================================
elif menu == "🔔 Alertas":
    st.title("🔔 Central de Alertas")
    
    df = carregar_ativos(st.session_state.user_id)
    
    if df.empty:
        st.info("Adicione ativos para configurar alertas")
    else:
        tab_alerta1, tab_alerta2 = st.tabs(["⚙️ Configurar", "📋 Meus Alertas"])
        
        with tab_alerta1:
            st.write("### Configurar Novo Alerta")
            
            col_a1, col_a2, col_a3 = st.columns(3)
            
            with col_a1:
                ticker_alerta = st.selectbox("Ativo", df['ticker'].tolist())
            with col_a2:
                tipo_alerta = st.selectbox("Tipo", ["Acima de R$", "Abaixo de R$"])
            with col_a3:
                preco_alerta = st.number_input("Preço alvo", min_value=0.01, value=10.0, step=1.0)
            
            preco_atual, status, _ = pegar_preco(ticker_alerta)
            if preco_atual:
                st.caption(f"💰 Preço atual: R$ {preco_atual:.2f}")
            
            if st.button("✅ Ativar Alerta", use_container_width=True):
                if salvar_alerta(st.session_state.user_id, ticker_alerta, tipo_alerta, preco_alerta):
                    st.success("Alerta configurado!")
                    st.rerun()
        
        with tab_alerta2:
            alertas = carregar_alertas(st.session_state.user_id)
            if not alertas:
                st.info("Nenhum alerta configurado")
            else:
                for alerta_id, alerta in list(alertas.items()):
                    preco_atual, _, _ = pegar_preco(alerta['ticker'])
                    
                    with st.container():
                        col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
                        
                        with col1:
                            st.write(f"**{alerta['ticker']}**")
                        with col2:
                            st.write(f"{alerta['tipo']} R$ {alerta['preco']:.2f}")
                        with col3:
                            if preco_atual:
                                st.write(f"Atual: R$ {preco_atual:.2f}")
                                
                                if (alerta['tipo'] == "Acima de R$" and preco_atual >= alerta['preco']) or \
                                   (alerta['tipo'] == "Abaixo de R$" and preco_atual <= alerta['preco']):
                                    st.warning("🚨 DISPAROU!")
                        with col4:
                            if st.button("🗑️", key=f"del_{alerta_id}"):
                                excluir_alerta(alerta_id)
                                st.rerun()
                        st.divider()

# ============================================
# 5. IMPOSTO RENDA
# ============================================
elif menu == "📝 Imposto Renda":
    st.title("📝 Imposto de Renda")
    
    tab_ir1, tab_ir2, tab_ir3 = st.tabs(["📊 Venda de Ações", "🏢 FIIs", "📋 Resumo Anual"])
    
    with tab_ir1:
        st.write("### Simulador de IR - Venda de Ações")
        
        col_ir1, col_ir2, col_ir3 = st.columns(3)
        
        with col_ir1:
            acao_venda = st.text_input("Ativo vendido", "PETR4").upper()
            qtd_venda = st.number_input("Quantidade vendida", min_value=0.0, value=100.0)
        
        with col_ir2:
            preco_compra = st.number_input("Preço médio de compra (R$)", min_value=0.01, value=30.0)
            preco_venda = st.number_input("Preço de venda (R$)", min_value=0.01, value=35.0)
        
        with col_ir3:
            total_vendas_mes = st.number_input("Total vendido no mês (R$)", min_value=0.0, value=15000.0)
        
        custo_total = qtd_venda * preco_compra
        venda_total = qtd_venda * preco_venda
        lucro = venda_total - custo_total
        
        st.write("---")
        
        if lucro > 0 and total_vendas_mes > 20000:
            ir_devido = lucro * 0.15
            st.error(f"IR devido: R$ {ir_devido:,.2f}")
            with st.expander("Código DARF"):
                st.code(f"""
                DARF - Código 6015
                Valor: R$ {ir_devido:.2f}
                Vencimento: Último dia útil do mês seguinte
                """)
        else:
            st.success("✅ ISENTO de IR")

    with tab_ir2:
        st.write("### Imposto sobre FIIs")
        
        col_f1, col_f2 = st.columns(2)
        
        with col_f1:
            dividendos = st.number_input("Dividendos recebidos (R$)", min_value=0.0, value=500.0)
        
        with col_f2:
            lucro_fii = st.number_input("Lucro com vendas (R$)", min_value=0.0, value=0.0)
        
        ir_total = (dividendos + lucro_fii) * 0.20
        
        if ir_total > 0:
            st.error(f"IR sobre FIIs: R$ {ir_total:,.2f}")# ============================================
# 6. PREÇO TETO
# ============================================
elif menu == "💰 Preço Teto":
    st.title("💰 Preço Teto - Método Bazin")
    st.caption("Baseado nos dividendos dos últimos 12 meses")
    
    df = carregar_ativos(st.session_state.user_id)
    
    if df.empty:
        st.info("Adicione ativos para calcular preço teto")
    else:
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            dy_desejado = st.slider("📊 Dividend Yield desejado (%)", 4, 12, 6) / 100
            st.caption("6% é o padrão do método Bazin")
        
        with col_t2:
            st.metric("DY Selecionado", f"{dy_desejado*100:.1f}%")
        
        resultados_teto = []
        for ticker in df['ticker']:
            preco_teto, msg = calcular_preco_teto_bazin(ticker, dy_desejado)
            preco_atual, _, _ = pegar_preco(ticker)
            
            if preco_teto and preco_atual:
                diferenca = (preco_teto - preco_atual) / preco_atual * 100
                if preco_atual <= preco_teto:
                    status = "✅ COMPRAR"
                    cor = "#00FF00"
                else:
                    status = "⏳ ESPERAR"
                    cor = "#FFA500"
                
                resultados_teto.append({
                    'Ticker': ticker,
                    'Preço Atual': preco_atual,
                    'Preço Teto': preco_teto,
                    'Diferença %': diferenca,
                    'Status': status
                })
        
        if resultados_teto:
            df_teto = pd.DataFrame(resultados_teto)
            st.dataframe(
                df_teto.style.format({
                    'Preço Atual': 'R$ {:.2f}',
                    'Preço Teto': 'R$ {:.2f}',
                    'Diferença %': '{:.1f}%'
                }).applymap(lambda x: f'color: {cor}' if isinstance(x, str) and x in ['✅ COMPRAR', '⏳ ESPERAR'] else '', subset=['Status']),
                use_container_width=True
            )

# ============================================
# 7. ANÁLISE AVANÇADA (PARTE 1)
# ============================================
elif menu == "📊 Análise Avançada":
    st.title("📊 Análise Avançada da Carteira")
    
    df = carregar_ativos(st.session_state.user_id)
    
    if df.empty:
        st.info("Adicione ativos para ver análises avançadas")
    else:
        tab_av1, tab_av2, tab_av3, tab_av4 = st.tabs(["📊 Correlação", "📈 Risco", "💰 Análise Preço", "📥 Exportar"])
        
        # TAB 1: MATRIZ DE CORRELAÇÃO
        with tab_av1:
            st.subheader("📊 Matriz de Correlação entre Ativos")
            st.caption("Mostra como os ativos se movem juntos. Valores próximos de 1 indicam alta correlação.")
            
            with st.spinner("Calculando correlações..."):
                correlacao, df_precos = calcular_matriz_correlacao(df['ticker'].tolist())
                
                if correlacao is not None:
                    fig = px.imshow(correlacao,
                                   text_auto=True,
                                   aspect="auto",
                                   color_continuous_scale='RdYlGn',
                                   title="Matriz de Correlação")
                    st.plotly_chart(fig, use_container_width=True)
                    
                    st.subheader("🔍 Insights de Correlação")
                    
                    for i in range(len(correlacao.columns)):
                        for j in range(i+1, len(correlacao.columns)):
                            corr_val = correlacao.iloc[i, j]
                            ativo1 = correlacao.columns[i]
                            ativo2 = correlacao.columns[j]
                            
                            if abs(corr_val) > 0.8:
                                st.warning(f"⚠️ **Alta correlação** entre {ativo1} e {ativo2}: {corr_val:.2f}")
                                st.caption("Isso significa que eles tendem a se mover na mesma direção. Pouca diversificação.")
                            elif abs(corr_val) < 0.3:
                                st.success(f"✅ **Baixa correlação** entre {ativo1} e {ativo2}: {corr_val:.2f}")
                                st.caption("Ótimo para diversificação! Eles se movem de forma independente.")
                else:
                    st.warning("Não foi possível calcular correlações (precisa de pelo menos 2 ativos com histórico)")        # TAB 2: ANÁLISE DE RISCO
        with tab_av2:
            st.subheader("📈 Análise de Risco")
            
            with st.spinner("Calculando métricas de risco..."):
                dados_risco = calcular_risco_retorno(df['ticker'].tolist())
                
                if dados_risco:
                    df_risco = pd.DataFrame(dados_risco).T
                    df_risco.columns = ['Retorno Anual %', 'Volatilidade %', 'Drawdown Máx %']
                    st.dataframe(df_risco.style.format('{:.2f}%'), use_container_width=True)
                    
                    fig = px.scatter(df_risco, x='Volatilidade %', y='Retorno Anual %',
                                    text=df_risco.index,
                                    title="Risco x Retorno",
                                    labels={'Volatilidade %': 'Risco (Volatilidade)', 'Retorno Anual %': 'Retorno Esperado'})
                    fig.update_traces(textposition='top center')
                    st.plotly_chart(fig, use_container_width=True)
        
        # TAB 3: ANÁLISE DE PREÇO (CARO/BARATO)
        with tab_av3:
            st.subheader("💰 Análise de Preço - Caro ou Barato?")
            
            ticker_selecionado = st.selectbox("Selecione um ativo para análise", df['ticker'].tolist())
            
            if ticker_selecionado:
                with st.spinner("Analisando dados históricos..."):
                    dados_hist = buscar_dados_historicos(ticker_selecionado)
                    status, msg_status, cor_status, explicacao, pontuacao = analisar_preco_ativo(ticker_selecionado, dados_hist)
                    
                    st.markdown(f"<h3 style='color:{cor_status}'>{msg_status}</h3>", unsafe_allow_html=True)
                    st.markdown(explicacao)
                    
                    if dados_hist:
                        fig = plotar_grafico_historico(dados_hist, ticker_selecionado)
                        if fig:
                            st.plotly_chart(fig, use_container_width=True)
        
        # TAB 4: EXPORTAÇÃO
        with tab_av4:
            st.subheader("📥 Exportar Dados")
            
            with st.spinner("Preparando dados para exportação..."):
                precos_info = []
                for ticker in df['ticker']:
                    preco, status, msg = pegar_preco(ticker)
                    precos_info.append({
                        'ticker': ticker,
                        'preco': preco if preco else 0,
                        'status': status
                    })
                
                df_precos = pd.DataFrame(precos_info)
                df_export = df.merge(df_precos, on='ticker')
                df_export['Patrimônio'] = df_export['qtd'] * df_export['preco']
                df_export['Custo Total'] = df_export['qtd'] * df_export['pm']
                df_export['Lucro/Prejuízo'] = df_export['Patrimônio'] - df_export['Custo Total']
                
                # Adicionar análise de preço
                analise_precos = []
                for ticker in df['ticker']:
                    dados_hist = buscar_dados_historicos(ticker)
                    if dados_hist:
                        status, _, _, _, _ = analisar_preco_ativo(ticker, dados_hist)
                        analise_precos.append({'ticker': ticker, 'analise': status})
                
                df_analise = pd.DataFrame(analise_precos) if analise_precos else None
            
            col_exp1, col_exp2 = st.columns(2)
            
            with col_exp1:
                st.write("**Exportar para Excel**")
                excel_data = exportar_para_excel(df_export, df_analise)
                st.download_button(
                    label="📥 Baixar Excel",
                    data=excel_data,
                    file_name=f"carteira_{datetime.now().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            
            with col_exp2:
                st.write("**Exportar para CSV**")
                csv_data = exportar_para_csv(df_export)
                st.download_button(
                    label="📥 Baixar CSV",
                    data=csv_data,
                    file_name=f"carteira_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            
            with st.expander("📋 Prévia dos dados"):
                st.dataframe(df_export, use_container_width=True)

# ============================================
# 8. GESTÃO DE CARTEIRA
# ============================================
elif menu == "⚙️ Gestão":
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
                if salvar_ativo(st.session_state.user_id, ticker, qtd, pm, setor):
                    st.balloons()
    
    with tab2:
        st.subheader("📋 Ativos Cadastrados")
        
        df_lista = carregar_ativos(st.session_state.user_id)
        
        if not df_lista.empty:
            if 'editando' not in st.session_state:
                st.session_state.editando = None
            
            for idx, row in df_lista.iterrows():
                with st.container():
                    col1, col2, col3 = st.columns([4, 1, 1])
                    
                    with col1:
                        st.write(f"**{row['ticker']}** | {row['qtd']:.2f} cotas | R$ {row['pm']:.2f} | {row['setor']}")
                    
                    with col2:
                        if st.button(f"✏️", key=f"edit_{row['ticker']}", use_container_width=True):
                            st.session_state.editando = row['ticker']
                            st.rerun()
                    
                    with col3:
                        if st.button(f"🗑️", key=f"del_{row['ticker']}", use_container_width=True):
                            if excluir_ativo(st.session_state.user_id, row['ticker']):
                                st.rerun()
                    
                    if st.session_state.editando == row['ticker']:
                        with st.form(key=f"form_edit_{row['ticker']}"):
                            nova_qtd = st.number_input("Quantidade", value=float(row['qtd']))
                            novo_pm = st.number_input("Preço Médio", value=float(row['pm']))
                            novo_setor = st.selectbox("Setor", 
                                                     ["Ações", "FII Papel", "FII Tijolo", "ETF", "Renda Fixa"],
                                                     index=["Ações", "FII Papel", "FII Tijolo", "ETF", "Renda Fixa"].index(row['setor']))
                            
                            col_s1, col_s2 = st.columns(2)
                            with col_s1:
                                if st.form_submit_button("Salvar"):
                                    if atualizar_ativo(st.session_state.user_id, row['ticker'], nova_qtd, novo_pm, novo_setor):
                                        st.session_state.editando = None
                                        st.rerun()
                            with col_s2:
                                if st.form_submit_button("Cancelar"):
                                    st.session_state.editando = None
                                    st.rerun()
                    
                    st.divider()
        else:
            st.info("📭 Nenhum ativo cadastrado.")
