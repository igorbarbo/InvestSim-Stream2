import matplotlib.pyplot as plt
from io import BytesIO
import pandas as pd

def gerar_pdf(df: pd.DataFrame, meses: int) -> BytesIO:
    """
    Gera um PDF com gráfico do patrimônio x meta.
    Reduz pontos para performance se meses > 360 (30 anos).
    """
    buffer = BytesIO()
    plt.figure(figsize=(8, 6))

    skip = 3 if meses > 360 else 1
    plt.plot(df["Mês"][::skip], df["Carteira"][::skip], marker='o', color='green', label="Carteira")
    plt.plot(df["Mês"][::skip], df["Meta"][::skip], linestyle='--', color='blue', label="Meta")
    
    plt.title("InvestSim Ultra Ninja Optimizado")
    plt.xlabel("Mês")
    plt.ylabel("Patrimônio (R$)")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    
    plt.savefig(buffer, format='pdf')
    buffer.seek(0)
    return buffer
