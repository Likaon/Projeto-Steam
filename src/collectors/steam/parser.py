def normalize_featured(payload: dict) -> dict:
    """
    Normaliza a estrutura dos dados de um item de jogo da Steam.
    - Renomeia 'id' para 'game_id'.
    - Converte preços de centavos para Reais (float).
    - Remove itens que não são jogos (sem 'id' ou 'type').
    """
    
    # CRITÉRIO 1: O item deve ter um 'id' para ser considerado um jogo/app
    if 'id' not in payload:
        return None
        
    # CRITÉRIO 2: O item deve ter um 'type' (0 para jogo é o mais comum, outros são DLC/vídeo)
    if 'type' not in payload:
        return None
        
    # CRITÉRIO 3: Se for um jogo, renomeamos o campo 'id' para 'game_id'
    payload['game_id'] = payload.pop('id')
    
    # CRITÉRIO 4: Converter preços de centavos (int) para float/Reais
    # A API da Steam geralmente usa centavos (ex: 2200 = R$ 22.00)
    for price_field in ['original_price', 'final_price']:
        if price_field in payload and isinstance(payload[price_field], int):
            # Certifique-se de que não estamos dividindo por zero e que é um preço real
            payload[price_field] = payload[price_field] / 100.0 if payload[price_field] > 0 else 0.0

    return payload

def parse_featured(data: dict) -> dict:
    """
    Extrai o dicionário de cada categoria que contém a lista de 'items' (jogos).
    A estrutura da API é {category: {id: X, name: Y, items: [...]}}.
    """
    normalized_categories = {}
    
    for category_key, category_data in data.items():
        # Verifica se o valor é um dicionário e contém a chave 'items'
        if isinstance(category_data, dict) and 'items' in category_data:
            items_list = category_data['items']
            
            # Verifica se 'items' é uma lista com pelo menos um item (opcional, mas bom)
            if isinstance(items_list, list):
                 
                # Retorna o dicionário da categoria
                normalized_categories[category_key] = category_data
                
    return normalized_categories