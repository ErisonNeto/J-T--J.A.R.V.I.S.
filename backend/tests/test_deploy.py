from sqlalchemy import select
from jarvis.deploy import bootstrap, memory_url, initialize
from jarvis.db import Store
from jarvis.security import digest
import pytest


def test_bootstrap_is_idempotent_and_hashed(tmp_path):
    store = Store("sqlite:///" + str(tmp_path / "memory.sqlite3"))
    token = "s" * 40
    bootstrap(store, token)
    bootstrap(store, token)
    with store.engine.connect() as c:
        rows = c.execute(select(store.users)).mappings().all()
        assert len(rows) == 1
        assert rows[0]["token_hash"] == digest(token)
        assert rows[0]["role"] == "manager"


def test_managed_memory_url_escapes_password(monkeypatch):
    monkeypatch.delenv("MEMORY_DATABASE_URL", raising=False)
    monkeypatch.setenv(
        "JARVIS_MEMORY_ADMIN_URL", "postgresql://owner:secret@host/jt_jarvis_memory"
    )
    monkeypatch.setenv("MEMORY_ROLE_PASSWORD", "a&b@c/d")
    url = memory_url()
    from sqlalchemy.engine import make_url

    parsed = make_url(url)
    assert parsed.password == "a&b@c/d"
    assert parsed.username == "jarvis_memory"
    assert parsed.drivername == "postgresql+psycopg"


def test_provisioning_rejects_operational_database(monkeypatch):
    monkeypatch.setenv(
        "JARVIS_MEMORY_ADMIN_URL", "postgresql://owner:secret@host/jt_indicadores"
    )
    monkeypatch.setenv("MEMORY_ROLE_PASSWORD", "s" * 40)
    monkeypatch.setenv("JARVIS_BOOTSTRAP_TOKEN", "t" * 40)
    monkeypatch.setenv("JARVIS_MANAGED_MEMORY", "true")
    with pytest.raises(ValueError, match="jt_jarvis_memory"):
        initialize()
