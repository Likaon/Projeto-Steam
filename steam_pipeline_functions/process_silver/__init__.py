import json
import datetime as dt
from pathlib import Path
import azure.functions as func

import sys
# garante que a raiz do projeto esteja no sys.path
root = Path(__file__).resolve().parents[2]
sys.path.append(str(root))

from src.collectors.steam import parser


def _now_iso():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def _bronze_dir():
    return Path(__file__).resolve().parents[2] / "src" / "processing" / "bronze"


def _silver_dir():
    return Path(__file__).resolve().parents[2] / "src" / "processing" / "silver"


def _list_bronze_files():
    d = _bronze_dir()
    d.mkdir(parents=True, exist_ok=True)
    return sorted(d.glob("raw_*.json"))


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


def main(timer: func.TimerRequest) -> None:
    print("[process_silver] start")
    bronze_files = _list_bronze_files()
    if not bronze_files:
        print("[process_silver] no bronze files found")
        return

    silver_items = []
    for bf in bronze_files:
        try:
            payload = _load_json(bf)
            
            # CORREÇÃO: Assume que o payload é a resposta bruta da API (dicionário de categorias).
            # Passamos o payload diretamente para o parser.
            normalized = parser.parse_featured(payload) 

            # Adiciona o envelope de metadados ao Silver
            silver_items.append({
                "source": "steam",
                "endpoint": "featuredcategories",
                "captured_at": _now_iso(), # Usamos o tempo atual
                "normalized_at": _now_iso(),
                "data": normalized,
            })
            
        except Exception as e:
            print(f"[process_silver] error reading or parsing {bf}: {e}")

    if silver_items:
        _save_silver(silver_items, tag="featured")
    else:
        print("[process_silver] nothing to save")