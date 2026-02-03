# Watcher

Dashboard de monitoramento de vendas e estoque integrado ao ERP Bling, construido com Streamlit.

## Funcionalidades

- **Vendas diarias/semanais/mensais** por SKU com graficos interativos (Plotly)
- **Ranking** dos 10 produtos mais vendidos
- **Estoque x Vendas** mensal com alerta para SKUs com estoque zerado ou negativo
- **Sincronizacao** automatica de pedidos de compra via API do Bling (OAuth 2.0)

## Stack

- **Frontend:** Streamlit
- **API:** FastAPI + Uvicorn
- **Banco de dados:** PostgreSQL (Supabase)
- **Integracao:** Bling ERP (OAuth 2.0, httpx)
- **Dados:** Pandas, Plotly

## Estrutura

```
├── app.py                   # Dashboard principal (vendas)
├── db.py                    # Conexao com o banco (Supabase)
├── requirements.txt
├── sync/
│   ├── api.py               # Endpoints FastAPI (OAuth + sync)
│   ├── bling.py             # Client da API Bling
│   └── models.py            # Operacoes de upsert no banco
├── pages/
│   ├── compras_vendas.py    # Pagina de estoque x vendas
│   └── vendas_categoria.py  # Vendas por categoria (filtros hierarquicos)
├── docker/
│   └── dashboard.Dockerfile # Imagem do Streamlit
├── docker-compose.yml
└── migrations/
    ├── 001_pedidos_compra.sql
    ├── 002_vw_compras_vendas_mensal.sql
    └── 003_vw_estoque_vendas_mensal.sql
```

## Configuracao

1. Clone o repositorio e crie um ambiente virtual:

```bash
python -m venv .venv
source .venv/bin/activate
```

2. Instale as dependencias:

```bash
pip install -r requirements.txt
```

3. Crie um arquivo `.env` na raiz com as variaveis:

```env
SUPA_HOST=<host>
SUPA_PORT=<port>
SUPA_DB=<database>
SUPA_USER=<user>
SUPA_PASS=<password>

BLING_CLIENT_ID=<client_id>
BLING_CLIENT_SECRET=<client_secret>
```

4. Execute as migrations no banco de dados (em ordem).

## Uso

**Dashboard:**

```bash
streamlit run app.py
```

**API de sincronizacao (Bling):**

```bash
uvicorn sync.api:app --reload
```

### Endpoints da API

| Endpoint | Metodo | Descricao |
|---|---|---|
| `/bling/auth` | GET | Inicia fluxo OAuth com o Bling |
| `/bling/callback` | GET | Callback do OAuth |
| `/sync/pedidos-compra` | POST | Sincroniza pedidos de compra |
| `/sync/status` | GET | Status da API e tokens |

## Docker

Para subir o dashboard via Docker Compose:

```bash
docker compose up -d --build
```

O dashboard estara disponivel em http://localhost:8501

Para parar:

```bash
docker compose down
```

O arquivo `.env` e carregado automaticamente pelo container.
