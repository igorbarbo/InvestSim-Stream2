# views/scanner.py
import streamlit as st
import pandas as pd
from config.settings import SCANNER_FIIS, SCANNER_ACOES, SCANNER_ETFS, SCANNER_BDRS, SCANNER_INTERNACIONAL
from services.preco_service import PrecoService
from services.analise_service import AnaliseService
from utils.exportacao import formatar_moeda

def show_scanner(user_id):
    st.title("🔍 Scanner de Oportunidades")
    st.markdown("### Encontre ativos baratos em diversas categorias")
    
    preco_service = PrecoService()
    analise_service = AnaliseService()
    
    categoria = st.selectbox("Escolha uma categoria", ["FIIs", "Ações", "ETFs Nacionais", "BDRs", "Internacional"])
    
    if categoria == "FIIs":
        tickers = SCANNER_FIIS
    elif categoria == "Ações":
        tickers = SCANNER_ACOES
    elif categoria == "ETFs Nacionais":
        tickers = SCANNER_ETFS
    elif categoria == "BDRs":
        tickers = SCANNER_BDRS
    else:
        tickers = SCANNER_INTERNACIONAL
    
    sensibilidade = st.select_slider("Sensibilidade", options=["Conservador", "Moderado", "Agressivo"], value="Moderado")
    
    if st.button("🔍 Analisar oportunidades", use_container_width=True):
        with st.spinner(f"Analisando {len(tickers)} ativos..."):
            resultados = []
            for ticker in tickers:
                dados = preco_service._buscar_dados_single(ticker)
                if dados.status == "ok":
                    resultado = analise_service.analisar(dados)
                    # Ajuste de sensibilidade (exemplo)
                    if sensibilidade == "Agressivo":
                        if resultado.pontuacao <= -30:
                            resultado.status = "oportunidade"
                            resultado.mensagem = "🔥 OPORTUNIDADE!"
                        elif resultado.pontuacao <= -10:
                            resultado.status = "barato"
                            resultado.mensagem = "👍 Barato"
                        elif resultado.pontuacao <= 15:
                            resultado.status = "neutro"
                            resultado.mensagem = "⚖️ Neutro"
                        else:
                            resultado.status = "caro"
                            resultado.mensagem = "❌ Caro"
                    resultados.append({
                        "Ticker": ticker,
                        "Status": resultado.status,
                        "Preço": dados.preco_atual,
                        "DY (%)": dados.dividend_yield if dados.dividend_yield else 0,
                        "Pontuação": resultado.pontuacao,
                        "Detalhes": resultado.explicacao[:100] + "..."
                    })
            if resultados:
                df = pd.DataFrame(resultados).sort_values("Pontuação", ascending=True)
                def colorir(row):
                    if row['Status'] == 'oportunidade':
                        return ['background-color: #006400; color: white']*len(row)
                    elif row['Status'] == 'barato':
                        return ['background-color: #32CD32; color: black']*len(row)
                    elif row['Status'] == 'neutro':
                        return ['background-color: #D4AF37; color: black']*len(row)
                    elif row['Status'] == 'atencao':
                        return ['background-color: #FFA500; color: black']*len(row)
                    elif row['Status'] == 'caro':
                        return ['background-color: #8B0000; color: white']*len(row)
                    return ['']*len(row)
                st.dataframe(
                    df.style.format({
                        "Preço": lambda x: formatar_moeda(x),
                        "DY (%)": "{:.2f}%",
                        "Pontuação": "{:.0f}"
                    }).apply(colorir, axis=1),
                    width='stretch'
                )
                
                ticker_detalhe = st.selectbox("Ver análise detalhada", df['Ticker'].tolist())
                if ticker_detalhe:
                    dados = preco_service._buscar_dados_single(ticker_detalhe)
                    resultado = analise_service.analisar(dados)
                    st.markdown(f"<h3 style='color:{resultado.cor}'>{resultado.mensagem}</h3>", unsafe_allow_html=True)
                    st.markdown(resultado.explicacao)
                    from utils.graficos import GraficoService
                    grafico = GraficoService.historico_precos(dados, ticker_detalhe)
                    if grafico:
                        st.plotly_chart(grafico, use_container_width=True)
            else:
                st.warning("Nenhum dado encontrado.")
