import pandas as pd
import yfinance as yf

def fetch_data():
    url = "https://docs.google.com/spreadsheets/d/1TWfuEvIn9YbSzEyFHKvWWD4XwppHhlj9Cm1RE6BweF8/gviz/tq?tqx=out:csv"
    try:
        df = pd.read_csv(url)
        df.columns = [c.strip() for c in df.columns]
        return df.dropna(subset=['Ativo'])
    except:
        return None

def sync_prices(df):
    tickers = df['Ativo'].unique().tolist()
    data = yf.download(tickers, period="1d", progress=False)['Close']
    p_dict = {t: float(data[t].iloc[-1] if len(tickers) > 1 else data.iloc[-1]) for t in tickers}
    df['Preço Atual'] = df['Ativo'].map(p_dict)
    df['Patrimônio'] = df['QTD'] * df['Preço Atual']
    df['Valorização %'] = (df['Preço Atual'] / df['Preço Médio'] - 1) * 100
    return df
  
