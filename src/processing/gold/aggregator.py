import json
from typing import Dict, Any, List
from datetime import datetime

def aggregate_featured_games(silver_data: Dict[str, Any], processing_time: str) -> List[Dict[str, Any]]:
    """
    Processa os dados estruturados da camada Silver e cria uma 
    lista de registros prontos para análise (Camada Gold/Tabela Fato).
    """
    
    gold_records = []
    
    try:
        # 1. Itera sobre a lista de documentos sob a chave "items"
        # O Silver está encapsulando cada registro em uma lista chamada "items".
        for doc in silver_data.get("items", []):
            
            # 2. Obtém a chave 'data' de cada documento do Silver
            raw_data = doc.get("data", {})
            
            # 3. Adaptação de Resiliência: O Silver tem uma chave "data" que é um dicionário.
            # O Gold precisa iterar sobre as chaves desse dicionário ('specials', 'top_sellers', etc.).
            # Usamos raw_data.get("categories", raw_data) se houver uma chave "categories" (como no seu exemplo), 
            # caso contrário, usamos o próprio raw_data.
            data_to_iterate = raw_data.get("categories", raw_data) 
            
            # Garante que data_to_iterate é um dicionário para iterar
            if not isinstance(data_to_iterate, dict):
                continue

            # Itera sobre as categorias reais que contêm listas de jogos
            for category_name_key, items_list in data_to_iterate.items():
                
                # Garante que estamos processando uma lista de jogos (e não chaves de metadados).
                if isinstance(items_list, list) and all(isinstance(item, dict) and 'id' in item for item in items_list):
                    
                    category_name = category_name_key
                    
                    for item in items_list:
                        
                        original_price_cents = item.get("original_price")
                        final_price_cents = item.get("final_price")
                        
                        # Campos básicos do jogo
                        record = {
                            "game_id": item.get("id"),
                            "game_name": item.get("name"),
                            "game_type": item.get("type"), 
                            "is_discounted": item.get("discounted"),
                            "discount_percent": item.get("discount_percent", 0),
                            
                            # Preços (convertidos para moeda)
                            "original_price": original_price_cents / 100 if original_price_cents is not None else None,
                            "final_price": final_price_cents / 100 if final_price_cents is not None else None,
                            
                            # Metadados de contexto (obtidos do 'doc' e não do 'item')
                            "category": category_name, 
                            "source": doc.get("source"),
                            "capture_date_utc": doc.get("captured_at"),
                            "processing_date_utc": processing_time
                        }
                        gold_records.append(record)

    except Exception as e:
        print(f"Error processing silver data for Gold layer: {e}")
        return []
        
    return gold_records

# Bloco para teste local
if __name__ == "__main__":
    # Simula a estrutura do arquivo Silver fornecido pelo usuário
    sample_silver = {
      "items": [
        {
          "source": "steam",
          "endpoint": "featuredcategories",
          "captured_at": "2025-11-27T15:22:44.437755+00:00",
          "normalized_at": "2025-11-28T15:10:00.075640+00:00",
          "data": {
            "categories": [
                # Estrutura vazia do seu exemplo
            ], 
            "specials": [ # Simulação de dados reais para teste
                 {
                    "id": 12345,
                    "type": 0,
                    "name": "Game A",
                    "discounted": True,
                    "discount_percent": 50,
                    "original_price": 4000,
                    "final_price": 2000
                },
            ]
          }
        }
      ]
    }
    
    current_time = datetime.utcnow().isoformat()
    result = aggregate_featured_games(sample_silver, current_time)
    print(f"Registros Gold gerados: {len(result)}")
    # print(json.dumps(result, indent=2))