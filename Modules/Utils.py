# Modules/utils.py
import pandas as pd
import io

def exportar_para_excel(df_carteira, df_analise=None):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_carteira.to_excel(writer, sheet_name='Carteira', index=False)
        if df_analise is not None:
            df_analise.to_excel(writer, sheet_name='Análise', index=False)
    output.seek(0)
    return output

def exportar_para_csv(df):
    return df.to_csv(index=False).encode('utf-8')
