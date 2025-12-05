import json
import datetime as dt
from pathlib import Path
import azure.functions as func

import sys
# Garante que o path do projeto seja acessível
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
    with outfile.open("w", encoding="utf-8") as f:
        json.dump({"items": items}, f, ensure_ascii=False, indent=2)
    print(f"[process_silver] wrote {outfile}")
    return outfile

def _validate_and_clean_game(game: dict) -> dict | None:
    """
    Valida e converte tipos de dados do registro do jogo usando o SCHEMA_FEATURED_GAME.
    Retorna o jogo limpo ou None se a validação falhar.
    """
    cleaned_game = {}
    
    for field, spec in SCHEMA_FEATURED_GAME.items():
        value = game.get(field)
        
        # 1. Checa Requisito
        if spec.get("required") and value is None:
            print(f"[process_silver:ValidationError] Registro descartado: Campo '{field}' é obrigatório, mas está ausente. {game.get('game_name', 'N/A')}")
            return None
        
        # 2. Conversão de Tipos (CRÍTICO)
        try:
            target_type = spec["type"]
            if value is not None:
                # Trata preços como float, mesmo que venham como string da API
                if field in ["original_price", "final_price"]:
                    # Remove possível prefixo de moeda ou vírgula se for o caso, e converte
                    value = str(value).replace('R$', '').replace(',', '.').strip()
                    cleaned_game[field] = float(value)
                elif target_type is bool and isinstance(value, int):
                    # Garante que booleanos 0/1 sejam bool
                    cleaned_game[field] = bool(value)
                else:
                    cleaned_game[field] = target_type(value)
            else:
                cleaned_game[field] = value # mantém None se não for obrigatório

        except (ValueError, TypeError):
            # Loga e descarta se a conversão de tipo falhar
            print(f"[process_silver:ValidationError] Registro descartado: Falha ao converter campo '{field}' para {spec['type'].__name__}. Valor: {value}. Jogo: {game.get('game_name', 'N/A')}")
            return None
            
    return cleaned_game


def main(timer: func.TimerRequest) -> None:
    print("[process_silver] start")
    
    bronze_files = _list_bronze_files() 
    
    if not bronze_files:
        print("[process_silver] no bronze files found")
        return

    final_game_list = []
    normalized_ts = _now_iso()

    for bf in bronze_files:
        try:
            payload = _load_json(bf)
            
            if not isinstance(payload, dict):
                 print(f"[process_silver] SKIPPING: {bf.name} não é um dicionário (formato de API).")
                 continue
            
            # Desaninhamento (flattening) usando o parser CORRIGIDO
            categories = parser.parse_featured(payload) 

            for category_name, category_data in categories.items():
                # Esta linha agora funciona, pois o parser.py garante que category_data tem 'items'
                for game in category_data.get("items", []): 
                    game["source"] = "steam"
                    game["endpoint"] = "featuredcategories"
                    game["category"] = category_name 
                    game["captured_at"] = normalized_ts
                    game["normalized_at"] = normalized_ts
                    final_game_list.append(game)
            
        except Exception as e:
            print(f"[process_silver] error reading or parsing {bf}: {e}")

    if final_game_list:
        _save_silver(final_game_list, tag="featured")
    else:
        print("[process_silver] nothing to save")