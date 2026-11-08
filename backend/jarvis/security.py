import hashlib
import time
from collections import defaultdict, deque
from threading import Lock
from fastapi import HTTPException
from sqlalchemy import select


def digest(token):
    return hashlib.sha256(token.encode()).hexdigest()


class Auth:
    def __init__(self, store, limit):
        self.store = store
        self.limit = limit
        self.requests = defaultdict(deque)
        self.lock = Lock()

    def authenticate(self, authorization):
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(401, "Autenticação necessária.")
        token = authorization[7:]
        if len(token) > 256 or len(token) < 32:
            raise HTTPException(401, "Credencial inválida.")
        with self.store.engine.connect() as conn:
            user = (
                conn.execute(
                    select(self.store.users).where(
                        self.store.users.c.token_hash == digest(token),
                        self.store.users.c.active.is_(True),
                    )
                )
                .mappings()
                .first()
            )
        if not user:
            raise HTTPException(401, "Credencial inválida.")
        with self.lock:
            q = self.requests[user["id"]]
            t = time.monotonic()
            while q and q[0] < t - 60:
                q.popleft()
            if len(q) >= self.limit:
                raise HTTPException(429, "Limite de uso. Aguarde um minuto.")
            q.append(t)
        return dict(user)


def require(user, *roles):
    if user["role"] not in roles:
        raise HTTPException(403, "Perfil sem permissão para esta ação.")
