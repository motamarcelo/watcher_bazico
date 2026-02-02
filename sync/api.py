import json
from urllib.parse import urlencode

from fastapi import FastAPI, Query
from fastapi.responses import RedirectResponse, StreamingResponse

from sync.bling import (
    BLING_AUTH_URL,
    BLING_CLIENT_ID,
    BLING_REDIRECT_URI,
    exchange_code,
    load_tokens,
    listar_pedidos_compra,
    buscar_pedido_compra,
)
from sync.models import upsert_pedidos_compra

app = FastAPI(title="Watcher Sync")


@app.get("/bling/auth")
def bling_auth():
    """Redireciona para a página de autorização do Bling."""
    params = urlencode({
        "response_type": "code",
        "client_id": BLING_CLIENT_ID,
        "redirect_uri": BLING_REDIRECT_URI,
        "state": "watcher",
    })
    return RedirectResponse(f"{BLING_AUTH_URL}?{params}")


@app.get("/bling/callback")
def bling_callback(code: str = Query(...), state: str = Query("")):
    """Recebe o code do OAuth2 e troca por tokens."""
    tokens = exchange_code(code)
    return {"message": "Autenticação concluída", "expires_in": tokens["expires_in"]}


def _sync_generator():
    """Busca e salva página por página, emitindo progresso."""
    import time

    pagina = 1
    total_inseridos = 0
    total_erros = 0
    total_pedidos = 0

    while True:
        resp = listar_pedidos_compra(pagina=pagina, limite=100)
        data = resp.get("data", [])
        if not data:
            break

        pedidos_detalhados = []
        for pedido_resumo in data:
            pedido_id = pedido_resumo.get("id")
            if pedido_id:
                time.sleep(0.35)
                try:
                    detalhe = buscar_pedido_compra(pedido_id)
                    pedidos_detalhados.append(detalhe.get("data", detalhe))
                except Exception as e:
                    total_erros += 1
                    yield json.dumps({"erro_fetch": str(e), "pedido_id": pedido_id}) + "\n"

        resultado = upsert_pedidos_compra(pedidos_detalhados)
        total_pedidos += resultado["total"]
        total_inseridos += resultado["inseridos"]
        total_erros += len(resultado["erros"])

        progresso = {
            "pagina": pagina,
            "pedidos_pagina": len(data),
            "inseridos_pagina": resultado["inseridos"],
            "erros_pagina": len(resultado["erros"]),
            "acumulado": {"total": total_pedidos, "inseridos": total_inseridos, "erros": total_erros},
        }
        yield json.dumps(progresso) + "\n"

        pagina += 1
        time.sleep(0.35)

    yield json.dumps({"concluido": True, "total": total_pedidos, "inseridos": total_inseridos, "erros": total_erros}) + "\n"


@app.post("/sync/pedidos-compra")
def sync_pedidos_compra():
    """Busca todos os pedidos de compra do Bling e salva no Supabase, com progresso."""
    return StreamingResponse(_sync_generator(), media_type="application/x-ndjson")


@app.get("/sync/status")
def status():
    """Health check e status dos tokens."""
    tokens = load_tokens()
    return {
        "status": "ok",
        "bling_autenticado": tokens is not None,
    }
