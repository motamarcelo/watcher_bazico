import os
import json
import time
import base64
from pathlib import Path

import httpx
from dotenv import load_dotenv

load_dotenv()

BLING_CLIENT_ID = os.getenv("BLING_CLIENT_ID", "")
BLING_CLIENT_SECRET = os.getenv("BLING_CLIENT_SECRET", "")
BLING_REDIRECT_URI = "http://localhost:8000/bling/callback"
BLING_AUTH_URL = "https://www.bling.com.br/Api/v3/oauth/authorize"
BLING_TOKEN_URL = "https://www.bling.com.br/Api/v3/oauth/token"
BLING_API_BASE = "https://www.bling.com.br/Api/v3"

TOKENS_FILE = Path(__file__).parent.parent / "bling_tokens.json"


def _basic_auth_header() -> str:
    credentials = f"{BLING_CLIENT_ID}:{BLING_CLIENT_SECRET}"
    encoded = base64.b64encode(credentials.encode()).decode()
    return f"Basic {encoded}"


def save_tokens(data: dict):
    tokens = {
        "access_token": data["access_token"],
        "refresh_token": data["refresh_token"],
        "expires_in": data.get("expires_in", 21600),
        "saved_at": time.time(),
    }
    TOKENS_FILE.write_text(json.dumps(tokens, indent=2))
    return tokens


def load_tokens() -> dict | None:
    if not TOKENS_FILE.exists():
        return None
    return json.loads(TOKENS_FILE.read_text())


def exchange_code(code: str) -> dict:
    """Troca o authorization code por access_token + refresh_token."""
    resp = httpx.post(
        BLING_TOKEN_URL,
        headers={"Authorization": _basic_auth_header()},
        json={"grant_type": "authorization_code", "code": code},
    )
    resp.raise_for_status()
    return save_tokens(resp.json())


def refresh_access_token() -> dict:
    """Renova o access_token usando o refresh_token."""
    tokens = load_tokens()
    if not tokens:
        raise RuntimeError("Nenhum token salvo. Faça a autenticação em /bling/auth")

    resp = httpx.post(
        BLING_TOKEN_URL,
        headers={"Authorization": _basic_auth_header()},
        json={"grant_type": "refresh_token", "refresh_token": tokens["refresh_token"]},
    )
    resp.raise_for_status()
    return save_tokens(resp.json())


def _get_access_token() -> str:
    tokens = load_tokens()
    if not tokens:
        raise RuntimeError("Nenhum token salvo. Faça a autenticação em /bling/auth")

    # Renova se expirou (com margem de 5 min)
    elapsed = time.time() - tokens["saved_at"]
    if elapsed >= tokens["expires_in"] - 300:
        tokens = refresh_access_token()

    return tokens["access_token"]


def _api_get(path: str, params: dict | None = None) -> dict:
    token = _get_access_token()
    resp = httpx.get(
        f"{BLING_API_BASE}{path}",
        headers={"Authorization": f"Bearer {token}"},
        params=params or {},
        timeout=30,
    )
    if resp.status_code == 401:
        # Token expirou, tenta renovar uma vez
        token = refresh_access_token()["access_token"]
        resp = httpx.get(
            f"{BLING_API_BASE}{path}",
            headers={"Authorization": f"Bearer {token}"},
            params=params or {},
            timeout=30,
        )
    resp.raise_for_status()
    return resp.json()


def listar_pedidos_compra(pagina: int = 1, limite: int = 100) -> dict:
    """Lista pedidos de compra (resumo)."""
    return _api_get("/pedidos/compras", {"pagina": pagina, "limite": limite})


def buscar_pedido_compra(id_pedido: int) -> dict:
    """Busca um pedido de compra com todos os detalhes (itens, parcelas, etc)."""
    return _api_get(f"/pedidos/compras/{id_pedido}")


def buscar_todos_pedidos_compra() -> list[dict]:
    """Busca todos os pedidos de compra com detalhes completos, paginando."""
    todos = []
    pagina = 1

    while True:
        resp = listar_pedidos_compra(pagina=pagina, limite=100)
        data = resp.get("data", [])
        if not data:
            break

        for pedido_resumo in data:
            pedido_id = pedido_resumo.get("id")
            if pedido_id:
                time.sleep(0.35)  # Rate limit: max 3 req/s
                detalhe = buscar_pedido_compra(pedido_id)
                todos.append(detalhe.get("data", detalhe))

        pagina += 1
        time.sleep(0.35)

    return todos
