class AnaliseService:
    @staticmethod
    def avaliar_oportunidade(preco_atual, preco_medio_ano, preco_teto=None):
        pontuacao = 0
        if preco_atual < preco_medio_ano * 0.9: pontuacao += 2 # 10% abaixo da média
        if preco_teto and preco_atual < preco_teto: pontuacao += 3 # Abaixo do teto Bazin
        
        if pontuacao >= 4: return "🔥 OPORTUNIDADE", "green"
        if pontuacao >= 2: return "👍 COMPRA", "blue"
        return "⚖️ AGUARDAR", "gray"
      
