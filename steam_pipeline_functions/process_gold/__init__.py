import logging
import json
import azure.functions as func
from datetime import datetime
import os
import glob
from pathlib import Path
import sys

# 🚨 CRÍTICO: Configuração do PATH para encontrar o módulo 'src'
# A função Azure precisa saber onde procurar 'src/processing/gold/aggregator.py'.
# Adicionamos a pasta raiz do projeto ao PATH do Python.
# O Path('..').resolve().parent.parent aponta para a pasta 'steam-data-pipeline'
sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))

# Importação do módulo de processamento Gold, agora que o PATH está configurado
try:
    from src.processing.gold.aggregator import aggregate_featured_games
    logging.info("Módulo 'aggregate_featured_games' importado com sucesso.")
except ImportError as e:
    logging.error(f"ERRO DE IMPORTAÇÃO: Não foi possível encontrar o módulo Gold. Verifique a estrutura de pastas e o PATH. Detalhe: {e}")
    # Se falhar, definimos uma função dummy para não travar o restante
    def aggregate_featured_games(data, time): return []


def main(mytimer: func.TimerRequest) -> None:
    utc_timestamp = datetime.utcnow().isoformat()
    processing_time = utc_timestamp
    logging.info('Python timer trigger function process_gold started at %s', processing_time)

    # 1. Configuração de Caminhos (Assume que silver_output/ e gold_output/ estão na raiz do projeto)
    ##BASE_PATH = Path(__file__).resolve().parent.parent.parent.parent 
    ##BASE_PATH = Path(__file__).resolve().parent.parent
    BASE_PATH = Path(__file__).resolve().parent.parent.parent
    SILVER_PATH = BASE_PATH / "src" / "processing" / "silver" ##/ "silver_output"
    GOLD_PATH = BASE_PATH / "gold_output"
    
    # 2. Cria o diretório de saída Gold se não existir
    GOLD_PATH.mkdir(exist_ok=True)
    
    # 3. Localiza o arquivo Silver mais recente
    # A função glob.glob busca todos os arquivos que correspondem ao padrão
    ##list_of_files = glob.glob(str(SILVER_PATH / "silver_featured_*.json"))
    list_of_files = glob.glob(str(SILVER_PATH / "silver_featured_*.json"))

    # 3. Localiza o arquivo Silver mais recente
    logging.info('Caminho de busca Silver: %s', SILVER_PATH) # <-- ADICIONE ESTA LINHA
    # A função glob.glob busca todos os arquivos que correspondem ao padrão
    list_of_files = glob.glob(str(SILVER_PATH / "silver_featured_*.json"))

    if not list_of_files:
        logging.warning("Nenhum arquivo Silver encontrado. Pulando processamento Gold.")
        return

    # Pega o arquivo criado mais recentemente (latest_file)
    latest_file = max(list_of_files, key=os.path.getctime)
    logging.info('Processando arquivo Silver mais recente: %s', latest_file)

    # 4. Lê o arquivo Silver
    try:
        with open(latest_file, 'r', encoding='utf-8') as f:
            silver_data = json.load(f)
    except Exception as e:
        logging.error(f"Erro ao ler arquivo Silver: {e}")
        return

    # 5. Processa os dados usando o módulo Gold
    gold_records = aggregate_featured_games(silver_data, processing_time)

    if not gold_records:
        logging.warning("A agregação Gold não retornou registros. Pulando a escrita.")
        return

    # 6. Salva o resultado agregado na camada Gold
    output_filename = f"gold_featured_facts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    output_path = GOLD_PATH / output_filename

    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(gold_records, f, indent=2, ensure_ascii=False)
        
        logging.info('Pipeline Gold finalizada. Registros salvos em: %s', output_path)

    except Exception as e:
        logging.error(f"Erro ao salvar arquivo Gold: {e}")


    if mytimer.past_due:
        logging.info('The timer is past due!')