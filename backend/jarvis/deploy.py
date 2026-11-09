"""Initialize only the new, dedicated Render memory database, then run the API."""

import os
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.engine import make_url
import psycopg
from psycopg import sql

from .db import Store, uid
from .security import digest


def memory_url():
    configured = os.getenv("MEMORY_DATABASE_URL")
    if configured:
        return configured
    admin = os.getenv("JARVIS_MEMORY_ADMIN_URL")
    password = os.getenv("MEMORY_ROLE_PASSWORD")
    if admin and password:
        return (
            make_url(admin)
            .set(
                drivername="postgresql+psycopg",
                username="jarvis_memory",
                password=password,
            )
            .render_as_string(hide_password=False)
        )
    return "sqlite:///./jarvis-dev.sqlite3"


def bootstrap(store, token):
    if len(token) < 32:
        raise ValueError(
            "Configure JARVIS_BOOTSTRAP_TOKEN com pelo menos 32 caracteres."
        )
    with store.engine.begin() as c:
        existing = c.execute(
            select(store.users.c.id).where(store.users.c.token_hash == digest(token))
        ).first()
        if existing:
            return
        user_id = uid()
        c.execute(
            store.users.insert().values(
                id=user_id,
                name="Orlean",
                role="manager",
                token_hash=digest(token),
                active=True,
            )
        )
        store.record(c, user_id, "user_created", user_id)


def initialize():
    admin = os.environ["JARVIS_MEMORY_ADMIN_URL"]
    password = os.environ["MEMORY_ROLE_PASSWORD"]
    token = os.environ["JARVIS_BOOTSTRAP_TOKEN"]
    if os.getenv("JARVIS_MANAGED_MEMORY") != "true":
        raise ValueError(
            "Inicializacao exige banco dedicado de memoria gerenciado pelo JARVIS."
        )
    parsed = make_url(admin)
    if parsed.database != "jt_jarvis_memory":
        raise ValueError("Inicializacao permitida somente no banco jt_jarvis_memory.")
    if len(password) < 32 or len(token) < 32:
        raise ValueError("Segredos de inicializacao ausentes ou muito curtos.")
    connection_url = parsed.set(drivername="postgresql").render_as_string(
        hide_password=False
    )
    with psycopg.connect(connection_url, autocommit=True, connect_timeout=15) as conn:
        conn.execute("SELECT pg_advisory_lock(77321501)")
        for version, filename in [
            (1, "001_memory.sql"),
            (2, "002_historical_scope.sql"),
            (3, "003_permissions.sql"),
        ]:
            exists = conn.execute(
                "SELECT to_regclass('jarvis.schema_migrations')"
            ).fetchone()[0]
            applied = (
                exists
                and conn.execute(
                    "SELECT 1 FROM jarvis.schema_migrations WHERE version=%s",
                    (version,),
                ).fetchone()
            )
            if not applied:
                conn.execute(
                    (
                        Path(__file__).resolve().parents[2] / "migrations" / filename
                    ).read_text()
                )
        conn.execute(
            sql.SQL("ALTER ROLE jarvis_memory PASSWORD {}").format(
                sql.Literal(password)
            )
        )
        # No operational tables are created or modified in this dedicated database.
        conn.execute("SELECT pg_advisory_unlock(77321501)")
    bootstrap(Store(memory_url()), token)
    print("Banco de memoria inicializado. Credenciais omitidas.", flush=True)


if __name__ == "__main__":
    initialize()
    # Keep the administrative connection credential out of the application process.
    os.environ["MEMORY_DATABASE_URL"] = memory_url()
    os.environ.pop("JARVIS_MEMORY_ADMIN_URL", None)
    os.environ.pop("MEMORY_ROLE_PASSWORD", None)
    os.environ.pop("JARVIS_BOOTSTRAP_TOKEN", None)
    os.execvp(
        "python",
        [
            "python",
            "-m",
            "uvicorn",
            "jarvis.main:create_app",
            "--factory",
            "--host",
            "0.0.0.0",
            "--port",
            os.environ.get("PORT", "10000"),
        ],
    )
