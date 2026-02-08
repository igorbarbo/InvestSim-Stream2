import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px

st.set_page_config(page_title="InvestSim Advisor PRO", layout="wide", page_icon="📝")

st.title("📝 Plano de Execução e Renda")

def carregar_dados():
    try:
        url = "https://docs.google.com/spreadsheets/d/1TWfuEvIn9YbSzEyFHKvWWD4XwppHhlj9Cm1RE6BweF8/gviz/tq?tqx=out:csv"
        df = pd.read_csv(url)
        df.columns = [c.strip() for c in df.columns]
        return df.dropna(subset=['Ativo'])
    except:
        return pd.DataFrame()

# --- SIDEBAR ---
st.sidebar.header("💰 Configuração do Aporte")
valor_aporte = st.sidebar.number_input("Aporte em Dinheiro Novo (R$)", value=3000.0)
taxa_mensal = 0.008 # Meta de 0,8%

df_pessoal = carregar_dados()

if not df_pessoal.empty:
    if st.button("🎯 Gerar Ordem de Compra"):
        with st.spinner("Sincronizando mercado..."):
            # 1. Dados e Câmbio
            cotacao_dolar = float(yf.download("USDBRL=X", period="1d", progress=False)['Close'].iloc[-1])
            tickers = df_pessoal['Ativo'].unique().tolist()
            dados_mercado = yf.download(tickers, period="1d", progress=False)['Close']
            precos_dict = {t: float(dados_mercado[t].iloc[-1] if len(tickers) > 1 else dados_mercado.iloc[-1]) for t in tickers}

            # 2. Lógica de Categorias
            def definir_tipo(ativo):
                if '11' in ativo and ativo.endswith('.SA'): return 'FII'
                if ativo.endswith('.SA'): return 'Ações Brasil'
                return 'Internacional'

            df_pessoal['Tipo'] = df_pessoal['Ativo'].apply(definir_tipo)
            df_pessoal['Preço BRL'] = df_pessoal['Ativo'].apply(lambda x: precos_dict.get(x, 0) * (cotacao_dolar if not x.endswith(".SA") else 1))
            df_pessoal['Total Atual'] = df_pessoal['QTD'] * df_pessoal['Preço BRL']
            
            patrimonio_atual = df_pessoal['Total Atual'].sum()
            renda_atual = patrimonio_atual * taxa_mensal
            
            # Somando o rendimento do mês ao aporte (Bola de Neve)
            total_disponivel = valor_aporte + renda_atual
            novo_patrimonio = patrimonio_atual + total_disponivel

            # 3. Rebalanceamento (40/30/30)
            metas = {'FII': 0.40, 'Ações Brasil': 0.30, 'Internacional': 0.30}
            contagem = df_pessoal['Tipo'].value_counts()
            df_pessoal['Meta Valor'] = df_pessoal['Tipo'].apply(lambda x: (novo_patrimonio * metas[x]) / contagem[x])
            df_pessoal['Aporte R$'] = (df_pessoal['Meta Valor'] - df_pessoal['Total Atual']).clip(lower=0)
            
            total_nec = df_pessoal['Aporte R$'].sum()
            if total_nec > 0:
                df_pessoal['Aporte R$'] = (df_pessoal['Aporte R$'] / total_nec) * total_disponivel
            
            df_pessoal['QTD Compra'] = (df_pessoal['Aporte R$'] / df_pessoal['Preço BRL']).astype(int)

            # --- EXIBIÇÃO ---
            st.success(f"### Dinheiro Total para Investir: R$ {total_disponivel:,.2f}")
            st.caption(f"(Aporte: R$ {valor_aporte:,.2f} + Dividendos do mês: R$ {renda_atual:,.2f})")

            # LISTA DE COMPRAS ESTILIZADA
            st.markdown("### 📋 ORDEM DE COMPRA (Para levar no App da Corretora)")
            ordem_texto = ""
            for _, row in df_pessoal[df_pessoal['QTD Compra'] > 0].iterrows():
                linha = f"✅ **{row['Ativo']}**: Comprar **{row['QTD Compra']}** cotas (Aprox. R$ {row['Aporte R$']:,.2f})"
                st.write(linha)
                ordem_texto += linha + "\n"

            # GRÁFICOS
            col1, col2 = st.columns(2)
            with col1:
                st.plotly_chart(px.pie(df_pessoal, values='Aporte R$', names='Ativo', title="Distribuição do Aporte Atual"), use_container_width=True)
            with col2:
                renda_nova = novo_patrimonio * taxa_mensal
                fig_bar = px.bar(x=['Renda Atual', 'Nova Renda'], y=[renda_atual, renda_nova], color=[0,1], title="Evolução da Renda Mensal")
                st.plotly_chart(fig_bar, use_container_width=True)

            # ÁREA DE EXPORTAÇÃO
            st.write("---")
            st.subheader("📩 Exportar Plano")
            st.text_area("Copie o texto abaixo e cole no seu WhatsApp ou Bloco de Notas:", 
                         value=f"PLANO DE APORTE - INVESTSIM\nTotal: R$ {total_disponivel:,.2f}\n\n" + ordem_texto.replace("**", ""), height=200)

else:
    st.info("Sincronize os dados para gerar seu plano de ação.")
    
