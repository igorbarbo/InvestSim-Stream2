# views/balanceamento.py
import streamlit as st
import pandas as pd
import plotly.express as px
from database.repository import AtivoRepository, MetaRepository
from services.preco_service import PrecoService
from utils.exportacao import formatar_moeda

def show_balanceamento(user_id):
    st.title("🔄 Balanceamento Inteligente da Carteira")
    st.markdown("### Mantenha sua carteira equilibrada")
    
    repo_ativo = AtivoRepository()
    repo_meta = MetaRepository()
    preco_service = PrecoService()
    
    ativos = repo_ativo.carregar_por_usuario(user_id)
    if not ativos:
        st.info("Adicione ativos primeiro.")
        return
    
    metas = repo_meta.carregar(user_id)
    if not metas:
        st.warning("Defina metas em 'Montar Carteira' primeiro.")
        return
    
    with st.spinner("Atualizando preços..."):
        dados_precos = preco_service.buscar_precos_batch([a['ticker'] for a in ativos])
    
    df = pd.DataFrame(ativos)
    df['preco'] = [dados_precos[t].preco_atual if dados_precos[t].status == 'ok' else 0 for t in df['ticker']]
    df['Patrimônio'] = df['qtd'] * df['preco']
    total = df['Patrimônio'].sum()
    
    alocacao_atual = df.groupby('setor')['Patrimônio'].sum().to_dict()
    comparacao = []
    for classe, meta_pct in metas.items():
        atual_valor = alocacao_atual.get(classe, 0)
        atual_pct = (atual_valor / total) * 100 if total > 0 else 0
        diff = atual_pct - meta_pct
        status = "🔴 Acima" if diff > 5 else "🟢 OK" if abs(diff) <= 5 else "🔵 Abaixo"
        comparacao.append({
            "Classe": classe,
            "Meta (%)": f"{meta_pct:.1f}%",
            "Atual (R$)": formatar_moeda(atual_valor),
            "Atual (%)": f"{atual_pct:.1f}%",
            "Diferença": f"{diff:+.1f}%",
            "Status": status
        })
    
    df_comp = pd.DataFrame(comparacao)
    st.subheader("📊 Alocação Atual vs. Meta")
    col1, col2 = st.columns(2)
    with col1:
        st.caption("Atual")
        fig1 = px.pie(values=[alocacao_atual.get(c,0) for c in metas.keys()], names=list(metas.keys()), hole=0.4)
        st.plotly_chart(fig1, use_container_width=True)
    with col2:
        st.caption("Meta")
        fig2 = px.pie(values=list(metas.values()), names=list(metas.keys()), hole=0.4)
        st.plotly_chart(fig2, use_container_width=True)
    
    st.dataframe(df_comp, width='stretch')
    
    st.subheader("💰 Recomendação de Aporte")
    valor_aporte = st.number_input("Quanto pretende aportar este mês? (R$)", min_value=0.0, value=500.0, step=100.0)
    if valor_aporte > 0:
        novo_total = total + valor_aporte
        recomendacoes = []
        for classe, meta_pct in metas.items():
            atual_valor = alocacao_atual.get(classe, 0)
            desejado = novo_total * meta_pct / 100
            diff = desejado - atual_valor
            if diff > 0:
                acao = "COMPRAR"
                sugestao = f"Aporte {formatar_moeda(diff)} em {classe}"
            elif diff < 0:
                acao = "VENDER"
                sugestao = f"Venda {formatar_moeda(-diff)} em {classe} (ou aguarde)"
            else:
                acao = "OK"
                sugestao = f"{classe} já está na meta"
            recomendacoes.append({
                "Classe": classe,
                "Atual": formatar_moeda(atual_valor),
                "Desejado": formatar_moeda(desejado),
                "Diferença": formatar_moeda(diff),
                "Ação": acao,
                "Sugestão": sugestao
            })
        st.dataframe(pd.DataFrame(recomendacoes), width='stretch')
    
    st.subheader("📉 Simulador de Estresse")
    queda = st.slider("Queda simulada nos preços (%)", 0, 50, 20) / 100
    novo_total_queda = total * (1 - queda)
    perda = total - novo_total_queda
    st.metric("Patrimônio após queda", formatar_moeda(novo_total_queda), delta=f"-{perda:,.2f}", delta_color="inverse")
    
    # Recomendação pós-crise
    st.info("💡 Em crise, mantenha a calma e evite vender. Use aportes para comprar nas classes abaixo da meta.")
