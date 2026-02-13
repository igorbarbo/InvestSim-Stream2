streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px

# Configuração Básica
st.set_page_config(page_title="Igorbarbo V6", layout="wide")

# Estilo Luxury que você gosta
st.markdown("""
    <style>
    .stApp { background-color: #05070A; color: white; }
    [data-testid="stMetricValue"] { color: #D4AF37 !important; }
    h1, h2, h3 { color: #D4AF37 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- MENU LATERAL ---
menu = st.sidebar.radio("Navegação", ["🏠 Dashboard", "💡 Sugestão de Aporte", "🎯 Projeção"])

# --- ABA: SUGESTÃO DE APORTE (A QUE TINHA SUMIDO) ---
if menu == "💡 Sugestão de Aporte":
    st.title("🎯 Onde investir meus R$ 150?")
    
    valor_disponivel = st.number_input("Valor para aporte (R$)", min_value=0.0, value=150.0)
    
    # Lista de ativos reais para sua meta de 0.75% a 1% ao mês
    dados_sugestao = [
        {"Ativo": "MXRF11", "Tipo": "FII Papel", "Preço": 10.50, "Yield AM": "1.02%"},
        {"Ativo": "CPTS11", "Tipo": "FII Papel", "Preço": 8.50, "Yield AM": "0.88%"},
        {"Ativo": "GALG11", "Tipo": "FII Logística", "Preço": 9.20, "Yield AM": "0.91%"},
        {"Ativo": "CDB Digital", "Tipo": "Renda Fixa", "Preço": 100.00, "Yield AM": "0.85%"}
    ]
    
    df_s = pd.DataFrame(dados_sugestao)
    df_s['Cotas Possíveis'] = (valor_disponivel // df_s['Preço']).astype(int)
    df_s['Renda Estimada (R$)'] = (df_s['Cotas Possíveis'] * df_s['Preço'] * 0.009) # Média de 0.9%

    st.write(f"### Com R$ {valor_disponivel:.2f}, você pode comprar:")
    st.table(df_s)
    
    st.info("💡 Dica: Foque em ativos 'Base 10' (preço perto de R$ 10) para conseguir comprar mais quantidades com R$ 150.")

# --- ABA: DASHBOARD ---
elif menu == "🏠 Dashboard":
    st.title("🏛️ Meu Patrimônio")
    st.write("Cadastre seus ativos para ver o gráfico aqui.")
    # (Aqui você pode manter sua lógica de db.get_assets se o seu db.py estiver funcionando)

# --- ABA: PROJEÇÃO ---
elif menu == "🎯 Projeção":
    st.title("🚀 Juros Compostos")
    aporte = st.number_input("Aporte Mensal", value=150)
    anos = st.slider("Anos", 1, 30, 10)
    
    meses = anos * 12
    taxa = 0.0085
    total = aporte * (((1 + taxa)**meses - 1) / taxa)
    
    st.metric("Patrimônio Estimado", f"R$ {total:,.2f}")
    st.warning(f"Isso renderia aprox. R$ {total * taxa:,.2f} por mês no futuro.")

