from datetime import date
from pathlib import Path
import sys
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from jarvis.config import Settings
from jarvis.db import Store, uid
from jarvis.security import digest
from jarvis.main import create_app
from jarvis.periods import default_period, comparisons
from jarvis.operations import aggregate, Operations, Unavailable
from jarvis.contracts import Filters


@pytest.fixture
def setup(tmp_path):
    s = Settings(
        memory_url="sqlite:///" + str(tmp_path / "memory.db"),
        operational_url="",
        allow_external=False,
        bridge_token="",
        environment="development",
        rate_limit=100,
    )
    db = Store(s.memory_url)
    tokens = {}
    with db.engine.begin() as c:
        for role in ["admin", "manager", "analyst", "developer"]:
            token = role + "x" * 40
            tokens[role] = {"Authorization": "Bearer " + token}
            c.execute(
                db.users.insert().values(
                    id=uid(),
                    name=role,
                    role=role,
                    token_hash=digest(token),
                    active=True,
                )
            )
    client = TestClient(create_app(s, db))
    return client, tokens, db, s


def memory():
    return dict(
        base_code="891108",
        indicator="sla",
        occurred_on="2026-11-04",
        explanation="Faltaram entregadores na operação.",
        evidence=["Relato do gestor Orlean"],
    )


def test_auth_and_profiles(setup):
    c, t, db, s = setup
    assert c.get("/api/memories").status_code == 401
    assert (
        c.post("/api/memories", headers=t["analyst"], json=memory()).status_code == 403
    )
    assert (
        c.post(
            "/api/chat",
            headers=t["manager"],
            json={"message": "crie código", "mode": "development"},
        ).status_code
        == 403
    )
    assert c.get("/api/audit", headers=t["manager"]).status_code == 403


def test_feedback_audit_and_version_conflict(setup):
    c, t, db, s = setup
    r = c.post("/api/memories", headers=t["manager"], json=memory())
    assert r.status_code == 201
    mid = r.json()["id"]
    assert r.json()["status"] == "hypothesis"
    patch = dict(
        version=1,
        status="confirmed",
        reason="Gestor confirmou a ocorrência.",
        evidence=[],
    )
    assert (
        c.patch("/api/memories/" + mid, headers=t["manager"], json=patch).status_code
        == 422
    )
    patch["evidence"] = ["Orlean confirmou a redução de entregadores."]
    assert (
        c.patch("/api/memories/" + mid, headers=t["manager"], json=patch).status_code
        == 200
    )
    assert (
        c.patch("/api/memories/" + mid, headers=t["manager"], json=patch).status_code
        == 409
    )
    rows = c.get("/api/memories", headers=t["analyst"]).json()
    assert rows[0]["confirmed_by"]
    assert (
        len(c.get("/api/memories/" + mid + "/revisions", headers=t["manager"]).json())
        == 1
    )
    assert len(c.get("/api/audit", headers=t["admin"]).json()) == 2
    patch.update(version=2, status="hypothesis", reason="Nova evidência exige revisão.")
    assert (
        c.patch("/api/memories/" + mid, headers=t["manager"], json=patch).status_code
        == 200
    )
    assert (
        c.get("/api/memories", headers=t["analyst"]).json()[0]["confirmed_by"] is None
    )


def test_conversation_persistence_isolation_and_outage(setup):
    c, t, db, s = setup
    r = c.post("/api/chat", headers=t["manager"], json={"message": "Como está o SLA?"})
    assert r.status_code == 200
    r = r.json()
    assert "não configurado" in r["answer"]
    cid = r["conversation_id"]
    assert c.get("/api/conversations/" + cid, headers=t["analyst"]).status_code == 404
    assert (
        c.post(
            "/api/chat",
            headers=t["analyst"],
            json={"message": "continue", "conversation_id": cid},
        ).status_code
        == 404
    )
    assert len(c.get("/api/conversations/" + cid, headers=t["manager"]).json()) == 2
    new = TestClient(create_app(s, Store(s.memory_url)))
    assert len(new.get("/api/conversations", headers=t["manager"]).json()) == 1


def test_validation_sql_injection_and_external_disabled(setup):
    c, t, _, _ = setup
    for filters in [
        {"indicator": "sla;drop table entregas"},
        {"base_code": "1' OR 1=1--"},
        {"start": "2026-11-08"},
        {"start": "2026-11-08", "end": "2026-11-01"},
    ]:
        assert (
            c.post("/api/analysis", headers=t["manager"], json=filters).status_code
            == 422
        )
    assert (
        c.post(
            "/api/investigations",
            headers=t["manager"],
            json={
                "city": "Castanhal",
                "state": "PA",
                "start": "2026-11-01",
                "end": "2026-11-05",
            },
        ).status_code
        == 503
    )
    assert (
        c.post(
            "/api/chat", headers=t["manager"], json={"message": "x" * 65000}
        ).status_code
        == 413
    )


def test_no_fabricated_metrics(setup):
    c, t, _, _ = setup
    assert (
        c.post(
            "/api/analysis", headers=t["manager"], json={"indicator": "sla"}
        ).status_code
        == 503
    )
    assert aggregate([], "sla")["value"] is None
    assert (
        aggregate([dict(day=date(2026, 1, 1), numerator=0, denominator=0)], "sla")[
            "value"
        ]
        is None
    )


def test_dates_monday_and_quality_month_boundary():
    assert default_period("sla", date(2026, 11, 9)) == (date(2026, 11, 8),) * 2
    assert default_period("1bd", date(2026, 11, 1)) == (date(2026, 10, 30),) * 2
    assert default_period("avaria", date(2026, 11, 8)) == (
        date(2026, 11, 2),
        date(2026, 11, 8),
    )
    r = comparisons(date(2026, 11, 9), date(2026, 11, 9))
    assert r["previous_week"] == (date(2026, 11, 2), date(2026, 11, 8))
    assert r["same_weekdays"] == (date(2026, 11, 2),) * 2


def test_weighted_percentages_and_financial_precision():
    rows = [
        dict(day=date(2026, 11, 1), numerator=90, denominator=100),
        dict(day=date(2026, 11, 2), numerator=1, denominator=10),
    ]
    assert aggregate(rows, "sla")["value"] == pytest.approx(100 * 91 / 110)
    assert aggregate(rows, "shipping")["value"] == pytest.approx(91 / 110)
    assert aggregate(rows, "5cd")["value"] == 45.5
    assert (
        aggregate(
            [dict(day=date(2026, 11, 1), numerator=12345, denominator=1)], "avaria"
        )["value"]
        == 123.45
    )
    assert aggregate(rows, "sem_mov")["above_10"] == 110


def test_scope_closed_by_default(setup):
    *_, s = setup
    assert not any(x["enabled"] for x in Operations(s).catalog())
    with pytest.raises(Unavailable):
        Operations(s).rows("csat", date.today(), date.today())


def test_retrieval_and_no_implicit_confirmation(setup):
    c, t, _, _ = setup
    c.post("/api/memories", headers=t["manager"], json=memory())
    assert len(c.get("/api/memories?q=entregadores", headers=t["manager"]).json()) == 1
    c.post(
        "/api/chat", headers=t["manager"], json={"message": "Sim, confirme a hipótese"}
    )
    assert (
        c.get("/api/memories", headers=t["manager"]).json()[0]["status"] == "hypothesis"
    )


def test_rate_limit_and_bridge(setup):
    _, t, db, s = setup
    s.rate_limit = 1
    s.bridge_token = "bridge" * 8
    c = TestClient(create_app(s, db))
    assert c.get("/api/status", headers=t["manager"]).status_code == 401
    headers = {**t["manager"], "X-Bridge-Token": s.bridge_token}
    assert c.get("/api/status", headers=headers).status_code == 200
    assert c.get("/api/status", headers=headers).status_code == 429


@pytest.mark.asyncio
async def test_planner_never_broadens_scope(setup):
    import json
    from jarvis.llm import Model

    *_, s = setup
    s.api_key = "test"
    s.model = "test"
    s.allow_external = True
    model = Model(s)

    async def fake(_):
        return (
            json.dumps(
                {
                    "clarification": None,
                    "queries": [
                        {
                            "indicator": "sla",
                            "start": None,
                            "end": None,
                            "base_code": None,
                            "manager": None,
                        }
                    ],
                }
            ),
            {},
        )

    model.request = fake
    plans, _ = await model.plan(
        "todos",
        Filters(
            base_code="891108",
            manager="Johan",
            start=date(2026, 11, 2),
            end=date(2026, 11, 3),
        ),
        [],
    )
    assert plans[0].base_code == "891108" and plans[0].manager == "Johan"
    assert plans[0].start == date(2026, 11, 2)


def test_llm_failure_does_not_write_partial_conversation(setup):
    c, t, db, s = setup
    from jarvis.llm import Model

    model = Model(s)

    async def fail(*a):
        raise RuntimeError("upstream")

    model.answer = fail
    c = TestClient(create_app(s, db, model=model))
    assert (
        c.post("/api/chat", headers=t["manager"], json={"message": "teste"}).status_code
        == 502
    )
    assert c.get("/api/conversations", headers=t["manager"]).json() == []


def test_rankings_comparisons_and_missing_days(setup):
    *_, s = setup
    op = Operations(s)
    op.rows = lambda *a: [
        {
            "day": date(2026, 11, 2),
            "base_code": "B",
            "base_name": "B",
            "manager": "Johan",
            "numerator": 50,
            "denominator": 100,
        },
        {
            "day": date(2026, 11, 2),
            "base_code": "A",
            "base_name": "A",
            "manager": "Johan",
            "numerator": 90,
            "denominator": 100,
        },
        {
            "day": date(2026, 10, 26),
            "base_code": "B",
            "base_name": "B",
            "manager": "Johan",
            "numerator": 80,
            "denominator": 100,
        },
    ]
    r = op.analyze(Filters(start=date(2026, 11, 2), end=date(2026, 11, 3)))
    assert r["value"] == 70
    assert r["ranking"][0]["base_code"] == "B"
    assert r["comparisons"]["same_weekdays"]["delta"] == -10
    assert r["days"] == 1 and r["latest_in_period"] == "2026-11-02"


def test_gateway_allows_only_fixed_routes_and_preserves_identity(monkeypatch):
    import httpx
    from jarvis.gateway import create_gateway

    monkeypatch.setenv("PREDATOR_API_URL", "https://predator.example.com")
    monkeypatch.setenv("BRIDGE_TOKEN", "bridge" * 8)
    captured = {}

    class FakeClient:
        def __init__(self, **kwargs):
            assert kwargs["follow_redirects"] is False

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def request(self, method, url, **kwargs):
            captured.update(url=url, **kwargs)
            return httpx.Response(200, json={"user": "test"})

    monkeypatch.setattr("jarvis.gateway.httpx.AsyncClient", FakeClient)
    c = TestClient(create_gateway())
    headers = {"Authorization": "Bearer " + "x" * 40}
    assert c.get("/api/query", headers=headers).status_code == 404
    assert c.get("/api/status").status_code == 401
    assert c.get("/api/status", headers=headers).status_code == 200
    assert captured["headers"]["Authorization"] == headers["Authorization"]
    assert captured["headers"]["X-Bridge-Token"] == "bridge" * 8
    assert captured["url"] == "https://predator.example.com/api/status"
    monkeypatch.setenv("PREDATOR_API_URL", "http://10.0.2.15:5432")
    with pytest.raises(ValueError):
        create_gateway()


@pytest.mark.asyncio
async def test_model_payload_is_stateless_and_extracts_output(setup, monkeypatch):
    import httpx
    from jarvis.llm import Model

    *_, s = setup
    s.api_key = "test"
    s.model = "test"
    s.allow_external = True

    class FakeClient:
        def __init__(self, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def post(self, url, **kwargs):
            assert url == "https://api.openai.com/v1/responses"
            assert kwargs["json"]["store"] is False
            return httpx.Response(
                200,
                request=httpx.Request("POST", url),
                json={
                    "status": "completed",
                    "output": [
                        {
                            "type": "message",
                            "content": [
                                {
                                    "type": "output_text",
                                    "text": "Resultado com evidências.",
                                }
                            ],
                        }
                    ],
                },
            )

    monkeypatch.setattr("jarvis.llm.httpx.AsyncClient", FakeClient)
    assert (
        await Model(s).answer("pergunta", [], {}, "operational")
        == "Resultado com evidências."
    )


def test_diagnostics_requires_manager_and_bridge(setup):
    client, tokens, db, settings = setup
    assert client.get('/api/diagnostics').status_code == 401
    assert client.get('/api/diagnostics', headers=tokens['analyst']).status_code == 403
    response = client.get('/api/diagnostics', headers=tokens['manager'])
    assert response.status_code == 200
    assert response.json()['memory'] == 'connected'
    assert not response.json()['checks']['jt_api']['ok']
