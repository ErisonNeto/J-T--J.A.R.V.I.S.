from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from datetime import date
import json
import httpx
import pytest
from jarvis.config import Settings
from jarvis.operations import Operations, Unavailable


def settings(**kw):
    return Settings(
        jt_api_url="https://example.test",
        jt_api_key="test-secret",
        operational_url="",
        approved="sla",
        **kw
    )


def test_bound_values_and_dates(monkeypatch):
    real = httpx.Client

    def handler(request):
        payload = json.loads(request.content)
        assert request.url.path == "/query"
        assert request.headers["X-API-Key"] == "test-secret"
        assert "x' OR 1=1" not in payload["sql"]
        assert "x' OR 1=1" in payload["params"]
        assert ":start" not in payload["sql"]
        assert "2026-11-01" in payload["params"]
        return httpx.Response(
            200, json={"rows": [["2026-11-01", "1", "Base", "Gestor", 9, 10]]}
        )

    monkeypatch.setattr(
        httpx, "Client", lambda **kw: real(transport=httpx.MockTransport(handler), **kw)
    )
    op = Operations(settings())
    assert op.catalog()[0]["enabled"]
    rows = op.rows("sla", date(2026, 11, 1), date(2026, 11, 1), base="x' OR 1=1")
    assert rows[0]["day"] == date(2026, 11, 1)


@pytest.mark.parametrize(
    "payload", [{}, {"rows": [["bad-date", "1", "B", "M", 1, 2]]}, {"rows": [[1, 2]]}]
)
def test_invalid_response_fails_closed(monkeypatch, payload):
    real = httpx.Client
    monkeypatch.setattr(
        httpx,
        "Client",
        lambda **kw: real(
            transport=httpx.MockTransport(lambda r: httpx.Response(200, json=payload)),
            **kw
        ),
    )
    with pytest.raises(Unavailable):
        Operations(settings()).rows("sla", date(2026, 11, 1), date(2026, 11, 1))


def test_approval_and_config():
    s = settings()
    s.approved = ""
    with pytest.raises(Unavailable):
        Operations(s).rows("sla", date(2026, 11, 1), date(2026, 11, 1))
    s.jt_api_url = "http://example.test"
    with pytest.raises(ValueError):
        s.validate()
