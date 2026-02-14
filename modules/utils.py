import pandas as pd
import io
import streamlit as st

def exportar_para_excel(df):
    """Converte o DataFrame da carteira em um arquivo Excel para download."""
    output = io.BytesIO()
    try:
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Minha_Carteira')
        return output.getvalue()
    except Exception as e:
        st.error(f"Erro ao gerar Excel: {e}")
        return None

def calcular_imposto_renda(tipo_ativo, valor_venda, custo_aquisicao):
    """
    Simula o cálculo de IR baseado na legislação brasileira:
    - Ações: Isento até R$ 20k/mês (vendas comuns). 15% sobre lucro acima disso.
    - FIIs: 20% sobre o lucro (sem isenção).
    """
    lucro = valor_venda - custo_aquisicao
    if lucro <= 0:
        return 0.0, "Prejuízo (Pode ser compensado no futuro)"
    
    if tipo_ativo == "Ações":
        if valor_venda <= 20000:
            return 0.0, "Isento (Venda total abaixo de R$ 20.000,00 no mês)"
        else:
            imposto = lucro * 0.15
            return imposto, f"DARF de 15% sobre o lucro (R$ {imposto:,.2f})"
            
    elif tipo_ativo == "FIIs":
        imposto = lucro * 0.20
        return imposto, f"DARF de 20% sobre o lucro (R$ {imposto:,.2f})"
    
    return 0.0, "Tipo de ativo não mapeado para IR"

def formatar_moeda(valor):
    """Formata números para o padrão de moeda brasileiro R$."""
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
  
