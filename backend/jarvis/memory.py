import re
from sqlalchemy import select


def retrieve(store, query, base_code=None):
    # Local lexical retrieval: no external embeddings until explicitly configured.
    terms = set(re.findall(r"\w+", query.lower()))
    stmt = select(store.memories).where(store.memories.c.status != "rejected")
    if base_code:
        stmt = stmt.where(store.memories.c.base_code == base_code)
    with store.engine.connect() as c:
        rows = [
            dict(r)
            for r in c.execute(
                stmt.order_by(store.memories.c.created_at.desc()).limit(500)
            ).mappings()
        ]
    scored = []
    for r in rows:
        words = set(re.findall(r"\w+", r["explanation"].lower()))
        score = len(terms & words) / max(1, len(terms | words))
        if score or base_code:
            scored.append((score, r))
    return [r for _, r in sorted(scored, key=lambda x: x[0], reverse=True)[:5]]
