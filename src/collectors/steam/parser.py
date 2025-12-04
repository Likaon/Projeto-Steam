def normalize_featured(payload: dict) -> dict:
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