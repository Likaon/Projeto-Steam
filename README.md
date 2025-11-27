# Steam Data Pipeline

## 📌 Visão Geral
Este projeto implementa uma **pipeline de captura de dados da Steam** usando **Azure Functions** e uma arquitetura em camadas (bronze → silver → gold).  
Até o momento, concluímos a **Etapa 2 (Captura)**, que organiza e valida os dados coletados da API da Steam.

---

## ✅ Etapa 1: Estrutura inicial
- Criação da pasta `steam_pipeline_functions` para armazenar as Functions do Azure.
- Configuração da Function **`capture_daily`** com timer trigger.
- Definição da pasta `src/processing/bronze` para persistência inicial dos dados brutos.

---

## ✅ Etapa 2: Captura organizada
### Estrutura criada em `src/collectors/steam`
- **`api.py`** → responsável por chamar a API da Steam (`featuredcategories`) e retornar os dados em um envelope padronizado.
- **`parser.py`** → módulo de normalização dos dados (por enquanto retorna o payload original).
- **`schemas.py`** → validação do envelope, garantindo que os campos obrigatórios (`source`, `endpoint`, `captured_at`, `data`) estejam presentes.
- **`__init__.py`** → módulo limpo para marcar a pasta como pacote Python.

### Ajustes na Function `capture_daily`
- Agora importa e usa `api.fetch_featured()` em vez de conter lógica própria de captura.
- Salva os resultados em arquivos JSON dentro de `src/processing/bronze`.

### Testes realizados
- Execução isolada do coletor com:
  ```bash
  python -m src.collectors.steam.api

  Resultado: envelope válido com dados da Steam (ex.: jogos em promoção).
- Execução da Function localmente com:
func start --port 7072

- Resultado: arquivos raw_YYYYMMDD_HHMMSS.json criados em src/processing/bronze


steam-data-pipeline/

├── steam_pipeline_functions/

│   └── capture_daily/

│       └── __init__.py

├── src/

│   ├── collectors/

│   │   └── steam/

│   │       ├── api.py

│   │       ├── parser.py

│   │       ├── schemas.py

│   │       └── __init__.py

│   └── processing/

│       └── bronze/

│           └── raw_*.json

