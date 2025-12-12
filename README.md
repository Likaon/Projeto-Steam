# Steam Data Pipeline

## Metas
- [x] Estrutura inicial do repositório
- [x] Coleta de dados brutos (Bronze)
- [x] Processamento Silver  (Desenvolvimento/Testes)
- [x] Processamento Gold   (em analise dos processos e inicio de integração com ajuste da etapa silver )
- [ ] Ingestão em streaming no Storage Account
- [ ] Parsing HTML com IA
- [ ] Processamento Spark (Big Data)
- [ ] Data Lakehouse (Delta Lake)
- [ ] Pipeline ELT com DLT
- [ ] Modelagem analítica (tabelas fato/dimensão)
- [ ] Monitoramento com Grafana



## 📌 Visão Geral
Este projeto implementa uma **pipeline de captura de dados da Steam** usando **Azure Functions** e uma arquitetura em camadas (bronze → silver → gold).  
Até o momento, concluí a **Etapa 2 (Captura)**, que organiza e valida os dados coletados da API da Steam.

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
    python -m src.collectors.steam.api

  Resultado: envelope válido com dados da Steam (ex.: jogos em promoção).
- Execução da Function localmente com:
func start --port 7072

- Resultado: arquivos raw_YYYYMMDD_HHMMSS.json criados em src/processing/bronze

```
steam-data-pipeline/
.
├── .github/                        # Configurações de CI/CD (GitHub Actions)
├── config/                         # Configurações globais e de ambiente
├── infra/                          # Código IaC (Terraform/Bicep) para o deploy na nuvem
├── scripts/                        # Scripts de utilidade e automação
├── tests/                          # Testes de unidade e integração
├── requirements.txt                # Dependências Python do projeto
├── local.settings.json             # Configurações locais do Azure Functions
|
├── src/
│   ├── collectors/
│   │   └── steam/
│   │       └── parser.py           # Módulo para desaninhamento e limpeza dos dados
│   │
│   └── processing/                 # Diretório de Armazenamento de Dados
│       ├── bronze/                 # CAMADA RAW: Dados brutos, inalterados.
│       ├── silver/                 # CAMADA LIMPA: Dados limpos, enriquecidos e tipados.
│       └── gold/                   # CAMADA DE NEGÓCIO: Dados agregados e prontos para consumo.
│
└── steam_pipeline_functions/       # Diretório das Funções Azure
    |
    ├── capture_daily/              # Função 1: ETAPA BRONZE (Extração/Coleta)
    │   ├── __init__.py             # Lógica Python de coleta da API
    │   └── function.json           # Agendamento Timer Trigger (Ex: a cada 1h)
    │
    ├── process_silver/             # Função 2: ETAPA SILVER (Limpeza/Enriquecimento)
    │   ├── __init__.py             # Lógica Python de Bronze -> Silver
    │   └── function.json           # Agendamento Timer Trigger (Ex: a cada 5min)
    │
    └── process_gold/               # Função 3: ETAPA GOLD (Transformação/Agregação)
        ├── __init__.py             # Lógica Python de Silver -> Gold (Seu código!)
        └── function.json           # Agendamento Timer Trigger (Ex: a cada 10min)
```
