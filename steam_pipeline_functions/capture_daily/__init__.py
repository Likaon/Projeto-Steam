import logging
import json
import datetime as dt
from pathlib import Path
import azure.functions as func
import sys

# CRÍTICO: Configuração do PATH
root = Path(__file__).resolve().parents[2]
sys.path.append(str(root))

# Importa o cliente real. SE FALHAR, É ERRO DE PATH OU DEPENDÊNCIA.
# Não há mais DummyClient aqui.
from src.collectors.steam import client as steam_client 


def _bronze_dir():
    # Define o diretório de saída para o Bronze
    return Path(__file__).resolve().parents[2] / "src" / "processing" / "bronze"


def _save_bronze(data):
    # Salva o dicionário de dados da API na camada Bronze
    out_dir = _bronze_dir()
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    outfile = out_dir / f"raw_featured_{ts}.json"
    
    # SALVA O DICIONÁRIO COMPLETO DA RESPOSTA DA API
    with outfile.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        
    logging.info(f"[capture_daily] Dados salvos em: {outfile}")
    return outfile


# FUNÇÃO PRINCIPAL: Usa 'timer'
def main(timer: func.TimerRequest) -> None:
    logging.info('Python timer trigger function capture_daily started at %s', dt.datetime.utcnow().isoformat())
    
    try:
        # 1. Coleta dos dados (Chamará a API real via api.py)
        featured_data = steam_client.get_featured_games()
        
        if not featured_data or not isinstance(featured_data, dict):
            logging.warning("[capture_daily] Coleta de dados falhou ou não retornou um dicionário. Pulando o salvamento.")
            return

        # 2. Salva na camada Bronze
        _save_bronze(featured_data)
        
        logging.info("[capture_daily] Coleta de dados Bronze finalizada.")
        
    except Exception as e:
        # Se falhar aqui, o erro é REAL: HTTP, rede, ou falta de dependências (requests)
        logging.error(f"[capture_daily] ERRO FATAL DE CONEXÃO/EXECUÇÃO DA API: {e}")