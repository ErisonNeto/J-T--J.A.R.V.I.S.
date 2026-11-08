"""Render gateway: forwards fixed API routes through authenticated HTTPS tunnel."""

import os, re
from urllib.parse import urlparse
import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response


def create_gateway():
    root = os.getenv("PREDATOR_API_URL", "").rstrip("/")
    token = os.getenv("BRIDGE_TOKEN", "")
    u = urlparse(root)
    if (
        u.scheme != "https"
        or not u.hostname
        or u.username
        or u.password
        or u.query
        or u.fragment
        or u.path not in ("", "/")
    ):
        raise ValueError(
            "PREDATOR_API_URL exige origem HTTPS sem caminho ou credenciais."
        )
    if len(token) < 32:
        raise ValueError("BRIDGE_TOKEN muito curto.")
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

    @app.get("/health")
    def health():
        return {"status": "alive", "role": "gateway"}

    @app.api_route("/api/{path:path}", methods=["GET", "POST", "PATCH"])
    async def relay(path: str, request: Request):
        if not re.fullmatch(
            r"(status|catalog|analysis|chat|investigations|audit|conversations(?:/[a-f0-9-]{36})?|memories(?:/[a-f0-9-]{36}(?:/revisions)?)?)",
            path,
        ):
            return JSONResponse({"detail": "Rota inválida."}, 404)
        auth = request.headers.get("authorization", "")
        if not auth.startswith("Bearer ") or not 39 <= len(auth) <= 263:
            return JSONResponse({"detail": "Autenticação necessária."}, 401)
        body = bytearray()
        async for chunk in request.stream():
            body.extend(chunk)
            if len(body) > 64000:
                return JSONResponse({"detail": "Requisição muito grande."}, 413)
        headers = {
            "Authorization": auth,
            "X-Bridge-Token": token,
            "Content-Type": "application/json",
        }
        for env, key in [
            ("CF_ACCESS_CLIENT_ID", "CF-Access-Client-Id"),
            ("CF_ACCESS_CLIENT_SECRET", "CF-Access-Client-Secret"),
        ]:
            if os.getenv(env):
                headers[key] = os.environ[env]
        try:
            async with httpx.AsyncClient(timeout=90, follow_redirects=False) as c:
                r = await c.request(
                    request.method,
                    root + "/api/" + path,
                    params=request.query_params,
                    headers=headers,
                    content=bytes(body),
                )
            if r.status_code >= 500 or "application/json" not in r.headers.get(
                "content-type", ""
            ):
                return JSONResponse(
                    {"detail": "Predator ou serviço local indisponível."}, 503
                )
            return Response(
                r.content,
                status_code=r.status_code,
                media_type="application/json",
                headers={
                    "Cache-Control": "no-store",
                    "X-Content-Type-Options": "nosniff",
                },
            )
        except httpx.HTTPError:
            return JSONResponse(
                {
                    "detail": "Predator desconectado. Tente novamente quando o serviço local estiver disponível."
                },
                503,
            )

    return app
