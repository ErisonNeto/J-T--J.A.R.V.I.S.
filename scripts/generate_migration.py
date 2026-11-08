"""Development-only SQL DDL generator; do not run against a database."""

import sys
from pathlib import Path
from sqlalchemy.schema import CreateTable, CreateIndex
from sqlalchemy.dialects import postgresql

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from jarvis.db import Store

root = Path(__file__).resolve().parents[1]
s = Store("postgresql+psycopg://unused:unused@localhost/unused")
sql = [
    "-- 001: run as migration owner, never the application role.",
    "BEGIN;",
    "CREATE SCHEMA IF NOT EXISTS jarvis;",
    "CREATE TABLE IF NOT EXISTS jarvis.schema_migrations (version integer PRIMARY KEY, applied_at timestamptz NOT NULL DEFAULT now());",
]
for t in s.metadata.sorted_tables:
    sql.append(str(CreateTable(t).compile(dialect=postgresql.dialect())) + ";")
    for i in t.indexes:
        sql.append(str(CreateIndex(i).compile(dialect=postgresql.dialect())) + ";")
sql.extend(
    [
        "ALTER TABLE jarvis.users ADD CONSTRAINT users_role CHECK (role IN ('admin','manager','analyst','developer'));",
        "ALTER TABLE jarvis.memories ADD CONSTRAINT memories_status CHECK (status IN ('hypothesis','confirmed','rejected'));",
        "ALTER TABLE jarvis.memories ADD CONSTRAINT confirmation_evidence CHECK (status != 'confirmed' OR (confirmed_by IS NOT NULL AND confirmed_at IS NOT NULL));",
        "INSERT INTO jarvis.schema_migrations(version) VALUES (1);",
        "COMMIT;",
    ]
)
(root / "migrations/001_memory.sql").write_text("\n".join(sql))
