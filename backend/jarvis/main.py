import json
import logging
import secrets
import time
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from sqlalchemy import select, text, update
from sqlalchemy.exc import SQLAlchemyError
from .config import Settings
from .db import Store, uid, now
from .security import Auth, require
from .contracts import Chat, Filters, MemoryCreate, MemoryChange, Investigation
from .operations import Operations, Unavailable
from .memory import retrieve
from .llm import Model

log = logging.getLogger("jarvis")


def create_app(settings=None, store=None, operations=None, model=None):
    s = settings or Settings()
    s.validate()
    db = store or Store(s.memory_url)
    op = operations or Operations(s)
    llm = model or Model(s)
    if s.environment == "production":
        from .permissions import check_public_writes

        check_public_writes(db.engine)
        if op.engine:
            check_public_writes(op.engine)
    auth = Auth(db, s.rate_limit)
    app = FastAPI(
        title="JARVIS · Regional Orlean",
        version="0.1.0",
        docs_url="/docs" if s.environment != "production" else None,
        redoc_url=None,
    )
    app.state.store = db

    @app.middleware("http")
    async def boundary(request, call_next):
        started = time.monotonic()
        trace = uid()
        if (
            s.bridge_token
            and not secrets.compare_digest(
                request.headers.get("x-bridge-token", ""), s.bridge_token
            )
            and request.url.path != "/health"
        ):
            return JSONResponse({"detail": "Origem não autorizada."}, status_code=401)
        # Streaming read bound, not just trusting Content-Length.
        body = bytearray()
        async for chunk in request.stream():
            body.extend(chunk)
            if len(body) > 64000:
                return JSONResponse(
                    {"detail": "Requisição muito grande."}, status_code=413
                )
        request._body = bytes(body)
        response = await call_next(request)
        response.headers.update(
            {
                "Cache-Control": "no-store",
                "X-Content-Type-Options": "nosniff",
                "X-Request-ID": trace,
            }
        )
        log.info(
            json.dumps(
                {
                    "event": "request",
                    "id": trace,
                    "method": request.method,
                    "status": response.status_code,
                    "ms": round((time.monotonic() - started) * 1000),
                }
            )
        )
        return response

    @app.exception_handler(SQLAlchemyError)
    async def database_error(request, exc):
        log.error(
            json.dumps({"event": "database_unavailable", "type": type(exc).__name__})
        )
        return JSONResponse(
            {"detail": "Memória indisponível. Confira a conexão com o Predator."},
            status_code=503,
        )

    def user(request: Request):
        return auth.authenticate(request.headers.get("authorization"))

    def own_conversation(c, cid, u):
        row = (
            c.execute(
                select(db.conversations).where(
                    db.conversations.c.id == cid, db.conversations.c.user_id == u["id"]
                )
            )
            .mappings()
            .first()
        )
        if not row:
            raise HTTPException(404, "Conversa não encontrada.")
        return row

    @app.get("/health")
    def health():
        return {"status": "alive", "service": "jarvis", "version": "0.1.0"}

    @app.get("/api/status")
    def status(u=Depends(user)):
        with db.engine.connect() as c:
            c.execute(text("SELECT 1"))
        return {
            "memory": "connected",
            "model": "configured" if llm.enabled() else "local",
            "operational": "configured_not_verified" if op.engine else "not_configured",
            "user": {"name": u["name"], "role": u["role"]},
        }

    @app.get("/api/catalog")
    def catalog(u=Depends(user)):
        return op.catalog()

    @app.get("/api/conversations")
    def conversations(u=Depends(user)):
        with db.engine.connect() as c:
            return [
                dict(r)
                for r in c.execute(
                    select(db.conversations)
                    .where(db.conversations.c.user_id == u["id"])
                    .order_by(db.conversations.c.created_at.desc())
                    .limit(100)
                ).mappings()
            ]

    @app.get("/api/conversations/{cid}")
    def messages(cid: str, u=Depends(user)):
        with db.engine.connect() as c:
            own_conversation(c, cid, u)
            return [
                dict(r)
                for r in c.execute(
                    select(db.messages)
                    .where(db.messages.c.conversation_id == cid)
                    .order_by(db.messages.c.created_at)
                ).mappings()
            ]

    @app.post("/api/analysis")
    def analysis(filters: Filters, u=Depends(user)):
        try:
            result = op.analyze(filters)
        except Unavailable as e:
            raise HTTPException(503, str(e))
        with db.engine.begin() as c:
            db.record(c, u["id"], "analysis", details=filters.model_dump(mode="json"))
        return result

    @app.post("/api/chat")
    async def chat(req: Chat, u=Depends(user)):
        if req.mode == "development":
            require(u, "admin", "developer")
        cid = req.conversation_id
        with db.engine.connect() as c:
            history = []
            if cid:
                own_conversation(c, cid, u)
                history = [
                    dict(r)
                    for r in c.execute(
                        select(db.messages)
                        .where(db.messages.c.conversation_id == cid)
                        .order_by(db.messages.c.created_at.desc())
                        .limit(10)
                    ).mappings()
                ][::-1]
        ctx = {
            "retrieval": "lexical",
            "memories": retrieve(db, req.message, req.filters.base_code),
        }
        clarification = None
        if req.mode == "operational":
            plans = [req.filters]
            if req.auto_route:
                try:
                    plans, clarification = await llm.plan(
                        req.message, req.filters, history
                    )
                except Exception:
                    raise HTTPException(
                        502,
                        "Não foi possível interpretar a consulta. Use os filtros manuais ou tente novamente.",
                    )
            ctx["analyses"] = []
            errors = []
            for plan in plans:
                try:
                    ctx["analyses"].append(op.analyze(plan))
                except Unavailable as e:
                    errors.append(str(e))
            if ctx["analyses"]:
                ctx["analysis"] = ctx["analyses"][0]
            if errors:
                ctx["unavailable"] = " ".join(errors)
        try:
            answer = clarification or await llm.answer(
                req.message, history, ctx, req.mode
            )
        except Exception:
            raise HTTPException(
                502,
                "O modelo não respondeu. Nenhuma mensagem desta tentativa foi salva. Tente novamente.",
            )
        with db.engine.begin() as c:
            if cid:
                own_conversation(c, cid, u)
            else:
                cid = uid()
                c.execute(
                    db.conversations.insert().values(
                        id=cid, user_id=u["id"], title=req.message[:120]
                    )
                )
            c.execute(
                db.messages.insert(),
                [
                    dict(
                        id=uid(),
                        conversation_id=cid,
                        role="user",
                        content=req.message,
                        payload={
                            "filters": req.filters.model_dump(mode="json"),
                            "mode": req.mode,
                        },
                    ),
                    dict(
                        id=uid(),
                        conversation_id=cid,
                        role="assistant",
                        content=answer,
                        payload=jsonable_encoder(ctx),
                    ),
                ],
            )
            db.record(
                c,
                u["id"],
                "chat",
                cid,
                {"mode": req.mode, "external_model": llm.enabled()},
            )
        return {"conversation_id": cid, "answer": answer, **ctx}

    @app.get("/api/memories")
    def memories(q: str = "", base_code: str | None = None, u=Depends(user)):
        if len(q) > 1000:
            raise HTTPException(422, "Busca muito longa.")
        if q:
            return retrieve(db, q, base_code)
        stmt = select(db.memories)
        if base_code:
            stmt = stmt.where(db.memories.c.base_code == base_code)
        with db.engine.connect() as c:
            return [
                dict(r)
                for r in c.execute(
                    stmt.order_by(db.memories.c.created_at.desc()).limit(100)
                ).mappings()
            ]

    @app.post("/api/memories", status_code=201)
    def remember(req: MemoryCreate, u=Depends(user)):
        require(u, "manager", "admin")
        mid = uid()
        with db.engine.begin() as c:
            c.execute(
                db.memories.insert().values(
                    id=mid,
                    author_id=u["id"],
                    status="hypothesis",
                    version=1,
                    **req.model_dump(mode="json")
                )
            )
            db.record(c, u["id"], "memory_created", mid)
        return {
            "id": mid,
            "status": "hypothesis",
            "version": 1,
            "message": "Hipótese registrada. Os parâmetros do modelo não foram alterados.",
        }

    @app.patch("/api/memories/{mid}")
    def correct(mid: str, req: MemoryChange, u=Depends(user)):
        require(u, "manager", "admin")
        if req.status == "confirmed" and not req.evidence:
            raise HTTPException(
                422, "Inclua evidência ou relato identificado para confirmar."
            )
        with db.engine.begin() as c:
            old = (
                c.execute(select(db.memories).where(db.memories.c.id == mid))
                .mappings()
                .first()
            )
            if not old:
                raise HTTPException(404, "Memória não encontrada.")
            if old["version"] != req.version:
                raise HTTPException(
                    409, "Memória alterada. Atualize antes de corrigir."
                )
            values = {
                "status": req.status,
                "version": req.version + 1,
                "evidence": req.evidence,
                "confirmed_by": u["id"] if req.status == "confirmed" else None,
                "confirmed_at": now() if req.status == "confirmed" else None,
            }
            for field in ["explanation", "actions", "outcome"]:
                if getattr(req, field) is not None:
                    values[field] = getattr(req, field)
            changed = c.execute(
                update(db.memories)
                .where(db.memories.c.id == mid, db.memories.c.version == req.version)
                .values(**values)
            )
            if changed.rowcount != 1:
                raise HTTPException(409, "Conflito de edição.")
            c.execute(
                db.revisions.insert().values(
                    id=uid(),
                    memory_id=mid,
                    actor_id=u["id"],
                    snapshot=jsonable_encoder(dict(old)),
                    reason=req.reason,
                )
            )
            db.record(
                c,
                u["id"],
                "memory_" + req.status,
                mid,
                {"version": req.version + 1, "reason": req.reason},
            )
        return {"id": mid, "version": req.version + 1, "status": req.status}

    @app.get("/api/memories/{mid}/revisions")
    def revisions(mid: str, u=Depends(user)):
        with db.engine.connect() as c:
            return [
                dict(r)
                for r in c.execute(
                    select(db.revisions)
                    .where(db.revisions.c.memory_id == mid)
                    .order_by(db.revisions.c.created_at)
                ).mappings()
            ]

    @app.post("/api/investigations")
    async def investigate(req: Investigation, u=Depends(user)):
        require(u, "admin", "manager")
        if not s.allow_search or not llm.enabled():
            raise HTTPException(
                503, "Pesquisa externa não configurada ou não autorizada."
            )
        try:
            result = await llm.investigate(req)
        except Exception:
            raise HTTPException(502, "Não foi possível consultar as fontes externas.")
        iid = uid()
        with db.engine.begin() as c:
            c.execute(
                db.investigations.insert().values(
                    id=iid,
                    actor_id=u["id"],
                    city=req.city + ", " + req.state,
                    start=str(req.start),
                    end=str(req.end),
                    result=result,
                )
            )
            db.record(c, u["id"], "investigation", iid)
        return {"id": iid, **result}

    @app.get("/api/audit")
    def audit(u=Depends(user)):
        require(u, "admin")
        with db.engine.connect() as c:
            return [
                dict(r)
                for r in c.execute(
                    select(db.audit).order_by(db.audit.c.created_at.desc()).limit(200)
                ).mappings()
            ]

    return app
