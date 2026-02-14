from pydantic import BaseModel, Field, field_validator
from decimal import Decimal
from typing import Optional
from datetime import datetime
import re

class Ativo(BaseModel):
    ticker: str = Field(..., description="Código do ativo")
    quantidade: Decimal = Field(..., gt=0)
    preco_medio: Decimal = Field(..., gt=0)
    setor: str = Field(...)
    data_aquisicao: Optional[datetime] = Field(default_factory=datetime.now)
    
    @field_validator('ticker')
    @classmethod
    def validar_ticker(cls, v):
        v = v.upper().strip()
        if not re.match(r'^[A-Z]{4}(3|4|11)$|^[A-Z]{1,5}$', v):
            raise ValueError(f"Ticker inválido: {v}")
        return v
    
    @property
    def ticker_yfinance(self) -> str:
        if self.ticker[-1].isdigit() and len(self.ticker) >= 5:
            return f"{self.ticker}.SA"
        return self.ticker
      
