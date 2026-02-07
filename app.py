import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="InvestSim Pro v3.0", layout="wide", page_icon="💎")

st.title("💎 Gestão de Carteira Inteligente")

def carregar_dados():
    try:
        url = "https://docs.google.com/spreadsheets/d/1TWfuEvIn9YbSzEyFHKvWWD4XwppHhlj9Cm1RE6BweF8/gviz/tq?tqx=out:csv"
        df = pd.read_csv(url)
        df.columns = [c.strip() for c in df.columns]
        if 'Ativo' in df.columns:
            df = df.dropna(subset=['Ativo'])
        return df
    except Exception as e:
        st.error(f"Erro na planilha: {e}")
        return pd.DataFrame()

df_pessoal = carregar_dados()

if not df_pessoal.empty:
    if st.button("🚀 Sincronizar e Analisar Mercado"):
        with st.spinner("Buscando cotações e conversão de câmbio..."):
            # 1. Buscar cotação do Dólar hoje
            try:
                cotacao_dolar = yf.download("USDBRL=X", period="1d", progress=False)['Close'].iloc[-1]
            except:
                cotacao_dolar = 5.00  # Fallback caso falhe
                st.warning("Não foi possível buscar o dólar atual. Usando R$ 5,00.")

            # 2. Buscar Ativos
            tickers = df_pessoal['Ativo'].unique().tolist()
            dados_mercado = yf.download(tickers, period="1d", progress=False)['Close']
            
            if len(tickers) == 1:
                precos_atuais = {tickers[0]: dados_mercado.iloc[-1]}
            else:
                precos_atuais = dados_mercado.iloc[-1].to_dict()

            # 3. Processamento Avançado
            df_pessoal['QTD'] = pd.to_numeric(df_pessoal['QTD'], errors='coerce').fillna(0)
            df_pessoal['Preço Médio'] = pd.to_numeric(df_pessoal['Preço Médio'], errors='coerce').fillna(0)
            
            # Lógica de Preço Atual e Moeda
            def converter_preco(ativo):
                preco = precos_atuais.get(ativo, 0)
                # Se não terminar com .SA e não for BDR (ex: AAPL), assume que é USD
                if not ativo.endswith(".SA") and len(ativo) <= 5:
                    return preco * cotacao_dolar, "USD"
                return preco, "BRL"

            df_pessoal[['Preço BRL', 'Moeda']] = df_pessoal['Ativo'].apply(lambda x: pd.Series(converter_preco(x)))
            
            df_pessoal['Investido'] = df_pessoal['QTD'] * df_pessoal['Preço Médio']
            df_pessoal['Atual'] = df_pessoal['QTD'] * df_pessoal['Preço BRL']
            df_pessoal['Lucro R$'] = df_pessoal['Atual'] - df_pessoal['Investido']
            df_pessoal['Lucro %'] = (df_pessoal['Lucro R$'] / df_pessoal['Investido']) * 100

            # --- MÉTRICAS DE TOPO ---
            total_investido = df_pessoal['Investido'].sum()
            total_atual = df_pessoal['Atual'].sum()
            lucro_total = total_atual - total_investido
            lucro_perc = (lucro_total / total_investido) * 100

            c1, c2, c3 = st.columns(3)
            c1.metric("Patrimônio Total", f"R$ {total_atual:,.2f}", f"{lucro_perc:.2f}%")
            c2.metric("Total Investido", f"R$ {total_investido:,.2f}")
            c3.metric("Lucro Líquido", f"R$ {lucro_total:,.2f}", delta_color="normal")

            # --- GRÁFICOS ---
            col_esq, col_dir = st.columns(2)
            
            with col_esq:
                fig_pizza = px.pie(df_pessoal, values='Atual', names='Ativo', hole=0.5, title="Alocação por Ativo")
                st.plotly_chart(fig_pizza, use_container_width=True)
            
            with col_dir:
                # Gráfico de Lucro por Ativo
                fig_lucro = px.bar(df_pessoal, x='Ativo', y='Lucro R$', 
                                  color='Lucro R$', color_continuous_scale='RdYlGn',
                                  title="Lucro/Prejuízo Individual")
                st.plotly_chart(fig_lucro, use_container_width=True)

            # --- TABELA DETALHADA ---
            st.subheader("📋 Detalhamento da Carteira")
            st.dataframe(df_pessoal.style.format({
                'Preço Médio': 'R$ {:.2f}',
                'Preço BRL': 'R$ {:.2f}',
                'Investido': 'R$ {:.2f}',
                'Atual': 'R$ {:.2f}',
                'Lucro R$': 'R$ {:.2f}',
                'Lucro %': '{:.2f}%'
            }))

else:
    st.warning("Configure a sua planilha corretamente para começar.")
    
