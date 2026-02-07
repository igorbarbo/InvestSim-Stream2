import streamlit as st
from streamlit_gsheets import GSheetsConnection
import yfinance as yf
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="InvestSim Pro", layout="wide")

# Função para garantir que o link esteja no formato correto de exportação
def get_csv_url(base_url):
    if "/edit" in base_url:
        return base_url.split("/edit")[0] + "/gviz/tq?tqx=out:csv"
    elif base_url.endswith("/"):
        return base_url + "gviz/tq?tqx=out:csv"
    else:
        return base_url + "/gviz/tq?tqx=out:csv"

st.title("📂 Minha Carteira Pessoal")

try:
    # Tenta conectar via Secrets
    url_base = "https://docs.google.com/spreadsheets/d/1TWfuEvIn9YbSzEyFHKvWWD4XwppHhlj9Cm1RE6BweF8"
    csv_url = get_csv_url(url_base)
    
    # Carrega os dados diretamente via Pandas (mais estável para evitar 404)
    df = pd.read_csv(csv_url)
    
    # Limpa colunas vazias
    df = df.dropna(subset=['Ativo'])

    if not df.empty:
        st.success("✅ Conectado à Planilha!")
        
        if st.button("📊 Atualizar Carteira"):
            tickers = df['Ativo'].unique().tolist()
            
            # Busca preços no Yahoo Finance
            with st.spinner("Atualizando cotações..."):
                precos = yf.download(tickers, period="1d", progress=False)['Close']
                
                # Se houver apenas um ticker, ajusta o formato
                if len(tickers) == 1:
                    precos_dict = {tickers[0]: precos.iloc[-1]}
                else:
                    precos_dict = precos.iloc[-1].to_dict()

                # Cálculos financeiros
                df['QTD'] = pd.to_numeric(df['QTD'], errors='coerce').fillna(0)
                df['Preço Médio'] = pd.to_numeric(df['Preço Médio'], errors='coerce').fillna(0)
                df['Preço Atual'] = df['Ativo'].map(precos_dict)
                df['Valor Total'] = df['QTD'] * df['Preço Atual']
                
                # Exibe Resultados
                st.metric("Patrimônio Total", f"R$ {df['Valor Total'].sum():,.2f}")
                
                fig = px.pie(df, values='Valor Total', names='Ativo', hole=0.4)
                st.plotly_chart(fig, use_container_width=True)
                
                st.dataframe(df)
    else:
        st.warning("Planilha encontrada, mas está vazia.")

except Exception as e:
    st.error(f"Erro ao acessar dados: {e}")
    st.info("Verifique se a planilha está como 'Qualquer pessoa com o link'.")
    
