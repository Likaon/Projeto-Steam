import json
import datetime as dt
from pathlib import Path
import azure.functions as func

import sys
root = Path(__file__).resolve().parents[2]
sys.path.append(str(root))

from src.collectors.steam import parser
from src.collectors.steam.Schemas.featured_schema import SCHEMA_FEATURED_GAME

def _now_iso():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def _bronze_dir():
    return Path(__file__).resolve().parents[2] / "src" / "processing" / "bronze"


def _silver_dir():
    return Path(__file__).resolve().parents[2] / "src" / "processing" / "silver"


def _list_bronze_files():
    d = _bronze_dir()
    d.mkdir(parents=True, exist_ok=True)
    return sorted(d.glob("raw_featured_*.json"))


def _load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _save_silver(items, tag="featured"):
    out_dir = _silver_dir()
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    outfile = out_dir / f"silver_{tag}_{ts}.json"
    # Agora salva a lista de dicionários
    with outfile.open("w", encoding="utf-8") as f:
        # Usa json.dump em vez de escrever a lista diretamente
        json.dump({"items": items}, f, ensure_ascii=False, indent=2) 
    print(f"[process_silver] wrote {outfile}")
    return outfile


def _validate_and_clean_game(game: dict) -> dict | None:
    """
    Valida e converte tipos de dados do registro do jogo usando o SCHEMA_FEATURED_GAME.
    Retorna o jogo limpo ou None se a validação falhar.
    """
    cleaned_game = {}
    
    # 1. VALIDAÇÃO CRÍTICA: Game ID deve existir e ser conversível
    game_id = game.get("game_id")
    if game_id is None:
        return None 
    try:
        cleaned_game["game_id"] = int(game_id)
    except ValueError:
        return None # Descartar se o ID não for um número

    # 2. Conversão e Limpeza dos demais campos
    for field, spec in SCHEMA_FEATURED_GAME.items():
        if field == "game_id":
            continue # Já validado

        value = game.get(field)
        
        try:
            target_type = spec["type"]
            
            if value is not None:
                if field in ["original_price", "final_price"]:
                    # Lógica robusta para preço: trata None, remove caracteres
                    value = str(value).replace('R$', '').replace(',', '.').strip()
                    cleaned_game[field] = float(value)
                elif target_type is bool and isinstance(value, int):
                    cleaned_game[field] = bool(value)
                else:
                    cleaned_game[field] = target_type(value)
            else:
                # Mantém o valor como None se não foi encontrado, mas pula a conversão
                cleaned_game[field] = None 

        except (ValueError, TypeError):
            # Se a conversão falhar (ex: 'abc' para float), registramos None e seguimos
            cleaned_game[field] = None
            
    # Garantir que todos os campos do schema estejam no dicionário, mesmo que None
    for field in SCHEMA_FEATURED_GAME.keys():
        if field not in cleaned_game:
            cleaned_game[field] = None
            
    return cleaned_game


def main(timer: func.TimerRequest) -> None:
    print("[process_silver] start")
    
    bronze_files = _list_bronze_files() 
    
    if not bronze_files:
        print("[process_silver] no bronze files found")
        return

    # MUDANÇA CRÍTICA: Usa um dicionário para garantir desduplicação por game_id
    # A última ocorrência de um game_id (a mais recente processada) prevalecerá.
    unique_games_dict = {}
    normalized_ts = _now_iso()

    for bf in bronze_files:
        try:
            payload = _load_json(bf)
            
            if not isinstance(payload, dict):
                 print(f"[process_silver] SKIPPING: {bf.name} não é um dicionário (formato de API).")
                 continue
            
            categories = parser.parse_featured(payload) 

            for category_name, category_data in categories.items():
                for game in category_data.get("items", []):
                    
                    ## normalizao renomeando id para game_id
                    normalized_game = parser.normalize_featured(game)
                    
                    # Se não for um jogo válido (ex: banner/spotlight), a normalização retorna None e pulamos
                    if not normalized_game:
                        continue                        

                    # 1. Adiciona Metadados
                    game["source"] = "steam"
                    game["endpoint"] = "featuredcategories"
                    game["category"] = category_name 
                    game["captured_at"] = normalized_ts
                    game["normalized_at"] = normalized_ts
                    
                    # 2. VALIDAÇÃO E LIMPEZA
                    validated_game = _validate_and_clean_game(game)
                    
                    if validated_game:
                        # 3. Adiciona ao dicionário de únicos, usando game_id como chave
                        game_id = validated_game.get("game_id")
                        if game_id:
                            # Isso desduplica. Se o jogo já estiver no dict, ele será sobrescrito.
                            unique_games_dict[game_id] = validated_game

        except Exception as e:
            print(f"[process_silver] error reading or parsing {bf}: {e}")

    # Converte o dicionário de volta para uma lista
    final_game_list = list(unique_games_dict.values())

    if final_game_list:
        _save_silver(final_game_list, tag="featured")
        print(f"[process_silver] {len(final_game_list)} registros válidos e únicos salvos.")
    else:
        print("[process_silver] nothing to save or all records failed validation")