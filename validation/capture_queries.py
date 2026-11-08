import json, sys
from pathlib import Path
from datetime import date

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from jarvis.operations import Operations, SPECS
from jarvis.config import Settings


class Fake:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def connect(self):
        return self

    def begin(self):
        return self

    def mappings(self):
        return []

    def execute(self, sql, params=None):
        if str(sql).startswith("SELECT"):
            self.sql = str(sql)
            self.params = params
        return self


op = Operations(Settings(operational_url="", approved=",".join(SPECS)))
op.engine = Fake()
queries = {}
for kind in SPECS:
    op.rows(kind, date(2026, 11, 1), date(2026, 11, 8))
    queries[kind] = {"sql": op.engine.sql, "params": op.engine.params}
Path(__file__).with_name("queries.json").write_text(json.dumps(queries, default=str))
