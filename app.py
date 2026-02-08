import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="InvestSim - Radar de Renda", layout="wide", page_icon="🏆")

def carregar_dados():
    url = "https://docs.google.com/spreadsheets/d/1TWfuEvIn9YbSzEyFHKvWWD4XwppHhlj9Cm1RE6BweF8/gviz/tq?tqx=out:csv"
    try:
        df = pd.read_csv(url)
        df.columns = [c.strip() for c in df.columns]
        return df.dropna(subset=['Ativo'])
    except:
        return pd.DataFrame(columns=['Ativo', 'QTD', 'Preço Médio'])

if 'df_carteira' not in st.session_state:
    st.session_state.df_carteira = carregar_dados()

# --- NAVEGAÇÃO POR ABAS ---
tab_dash, tab_radar, tab_edit = st.tabs(["📊 Dashboard", "🏆 Radar de Renda", "📂 Gerenciar Ativos"])

# --- ABA 1: DASHBOARD (Mantendo a inteligência anterior) ---
with tab_dash:
    st.title("💎 Gestão de Carteira")
    # ... (Seu código anterior de cálculos e gráficos aqui)
    st.info("💡 Dica: Consulte a aba 'Radar de Renda' para ver sua eficiência de dividendos.")

# --- ABA 2: RADAR DE RENDA (NOVIDADE) ---
with tab_radar:
    st.title("🏆 Eficiência de Dividendos")
    
    if st.button("🔍 Calcular Minha Rentabilidade Real"):
        with st.spinner("Analisando dividendos históricos..."):
            df_radar = st.session_state.df_carteira.copy()
            tickers = df_radar['Ativo'].unique().tolist()
            
            # 1. Puxar dados de dividendos dos últimos 12 meses
            dados_div = {}
            for t in tickers:
                try:
                    stock = yf.Ticker(t)
                    # Soma dividendos dos últimos 12 meses
                    hist_div = stock.dividends
                    if not hist_div.empty:
                        dados_div[t] = hist_div.tail(365).sum()
                    else:
                        dados_div[t] = 0.0
                except:
                    dados_div[t] = 0.0

            # 2. Cálculos de Yield on Cost (YoC)
            df_radar['Div_Anual_Por_Cota'] = df_radar['Ativo'].map(dados_div)
            df_radar['Renda_Anual_Total'] = df_radar['QTD'] * df_radar['Div_Anual_Por_Cota']
            
            # Yield On Cost = (Dividendos Anuais / Preço Médio Pago)
            df_radar['YoC (%)'] = (df_radar['Div_Anual_Por_Cota'] / df_radar['Preço Médio']) * 100
            
            # 3. Exibição de Métricas de Renda
            total_renda_ano = df_radar['Renda_Anual_Total'].sum()
            renda_media_mes = total_renda_ano / 12
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Renda Anual Estimada", f"R$ {total_renda_ano:,.2f}")
            c2.metric("Renda Média Mensal", f"R$ {renda_media_mes:,.2f}")
            c3.metric("YoC Médio da Carteira", f"{df_radar['YoC (%)'].mean():,.2f}%")

            # Gráfico de Projeção de Renda por Ativo
            st.write("---")
            fig_renda = px.bar(df_radar, x='Ativo', y='Renda_Anual_Total', 
                               color='YoC (%)', title="Quem mais coloca dinheiro no seu bolso (Anual)",
                               labels={'Renda_Anual_Total': 'Renda Total (R$)'},
                               color_continuous_scale='Greens')
            st.plotly_chart(fig_renda, use_container_width=True)

            # Tabela de Eficiência
            st.write("### 📊 Tabela de Eficiência (Dividendos)")
            st.dataframe(df_radar[['Ativo', 'QTD', 'Preço Médio', 'Div_Anual_Por_Cota', 'YoC (%)']].style.format({
                'Preço Médio': 'R$ {:.2f}', 
                'Div_Anual_Por_Cota': 'R$ {:.2f}',
                'YoC (%)': '{:.2f}%'
            }))
            
            st.info("""
            **O que é o Yield on Cost (YoC)?** É a rentabilidade dos dividendos baseada no preço que você pagou. 
            Se você comprou uma ação por R$ 10 e ela paga R$ 1 de dividendo, seu YoC é 10%. 
            Mesmo que a ação suba para R$ 20, seu YoC continua sendo 10% sobre o seu suado dinheiro!
            """)

# --- ABA 3: EDITOR (Mantendo sua funcionalidade de edição) ---
with tab_edit:
    st.title("📂 Gerenciar Ativos")
    df_editado = st.data_editor(st.session_state.df_carteira, num_rows="dynamic", use_container_width=True)
    if st.button("💾 Aplicar Mudanças"):
        st.session_state.df_carteira = df_editado
        st.success("Dados atualizados!")
        
