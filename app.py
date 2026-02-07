import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="InvestSim Pro", layout="wide", page_icon="📈")

# --- FUNÇÃO PARA CONVERSÃO DE LINK (RESOLVE ERRO 404) ---
def formatar_link_google(url):
    # Transforma o link de edição em um link de exportação direta de dados
    if "/edit" in url:
        return url.split("/edit")[0] + "/gviz/tq?tqx=out:csv"
    return url

# --- INTERFACE PRINCIPAL ---
st.title("📂 Minha Carteira Pessoal")

# Tenta carregar os dados
try:
    # 1. Tenta carregar via Secrets (Conector Oficial)
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read()
    
    # Se falhar ou vier vazio, tenta via URL direta (Método de Backup)
    if df is None or df.empty:
        url_direta = "https://docs.google.com/spreadsheets/d/1TWfuEvIn9YbSzEyFHKvWWD4XwppHhlj9Cm1RE6BweF8/gviz/tq?tqx=out:csv"
        df = pd.read_csv(url_direta)

    # Limpeza de dados
    df = df.dropna(subset=['Ativo'])

    if not df.empty:
        st.success("✅ Planilha conectada com sucesso!")
        
        if st.button("📊 Atualizar Patrimônio e Lucro"):
            with st.spinner("Buscando cotações no Yahoo Finance..."):
                # Lista de ativos
                tickers = df['Ativo'].unique().tolist()
                
                # Busca preços atuais
                dados_mercado = yf.download(tickers, period="1d", progress=False)['Close']
                
                # Se for apenas um ativo, o yfinance retorna uma série
                if len(tickers) == 1:
                    precos_atuais = {tickers[0]: dados_mercado.iloc[-1]}
                else:
                    precos_atuais = dados_mercado.iloc[-1].to_dict()

                # Cálculos
                df['QTD'] = pd.to_numeric(df['QTD'], errors='coerce').fillna(0)
                df['Preço Médio'] = pd.to_numeric(df['Preço Médio'], errors='coerce').fillna(0)
                df['Preço Atual'] = df['Ativo'].map(precos_atuais)
                
                df['Total Investido'] = df['QTD'] * df['Preço Médio']
                df['Valor de Mercado'] = df['QTD'] * df['Preço Atual']
                df['Lucro/Prejuízo'] = df['Valor de Mercado'] - df['Total Investido']

                # Métricas
                total_patrimonio = df['Valor de Mercado'].sum()
                c1, c2 = st.columns(2)
                c1.metric("Patrimônio Total", f"R$ {total_patrimonio:,.2f}")
                
                # Gráfico de Pizza
                fig = px.pie(df, values='Valor de Mercado', names='Ativo', title="Divisão da Carteira")
                st.plotly_chart(fig, use_container_width=True)

                # Tabela detalhada
                st.dataframe(df.style.format({
                    'Preço Médio': 'R$ {:.2f}', 
                    'Preço Atual': 'R$ {:.2f}',
                    'Total Investido': 'R$ {:.2f}',
                    'Valor de Mercado': 'R$ {:.2f}'
                }))
    else:
        st.warning("A planilha foi encontrada, mas as linhas estão vazias.")

except Exception as e:
    st.error(f"Erro de Conexão: {e}")
    st.info("Certifique-se de que a planilha está em 'Qualquer pessoa com o link'.")
    
