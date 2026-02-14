import yfinance as yf
from concurrent.futures import ThreadPoolExecutor, as_completed
from config.settings import settings

class PrecoService:
    def __init__(self):
        self.workers = settings.MAX_WORKERS

    def buscar_precos_batch(self, tickers):
        resultados = {}
        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            futures = {executor.submit(self._get_price, t): t for t in tickers}
            for future in as_completed(futures):
                ticker = futures[future]
                resultados[ticker] = future.result()
        return resultados

    def _get_price(self, ticker):
        try:
            t_yf = f"{ticker}.SA" if ticker[-1].isdigit() else ticker
            data = yf.Ticker(t_yf).history(period="1d")
            return data['Close'].iloc[-1] if not data.empty else 0
        except:
            return 0
          
