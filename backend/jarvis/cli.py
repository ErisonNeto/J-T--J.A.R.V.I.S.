import argparse, csv, secrets
from pathlib import Path
from sqlalchemy import text, select
from .config import Settings
from .db import Store, uid
from .security import digest


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    u = sub.add_parser("user")
    u.add_argument("--name", required=True)
    u.add_argument(
        "--role", choices=["admin", "manager", "analyst", "developer"], required=True
    )
    sub.add_parser("discover")
    sub.add_parser("retention-preview")
    a = sub.add_parser("assignments")
    a.add_argument("csv_file")
    args = p.parse_args()
    s = Settings()
    db = Store(s.memory_url)
    if args.cmd == "user":
        token = secrets.token_urlsafe(36)
        with db.engine.begin() as c:
            user_id = uid()
            c.execute(
                db.users.insert().values(
                    id=user_id,
                    name=args.name,
                    role=args.role,
                    token_hash=digest(token),
                    active=True,
                )
            )
            db.record(c, user_id, "user_created", user_id)
        print("Guarde esta chave individual; será exibida somente agora:")
        print(token)
    elif args.cmd == "discover":
        from .operations import Operations

        op = Operations(s)
        if not op.engine:
            raise SystemExit("Configure OPERATIONAL_DATABASE_URL.")
        with op.engine.connect() as c:
            with c.begin():
                c.execute(text("SET TRANSACTION READ ONLY"))
                rows = c.execute(
                    text(
                        "SELECT table_schema,table_name,column_name,data_type FROM information_schema.columns WHERE table_schema='public' ORDER BY table_name,ordinal_position"
                    )
                )
                writer = csv.writer(__import__("sys").stdout)
                writer.writerow(["schema", "table", "column", "type"])
                writer.writerows(rows)
    elif args.cmd == "assignments":
        if not db.pg:
            raise SystemExit("Gestão histórica exige PostgreSQL e migration 002.")
        with open(args.csv_file, encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))
        with db.engine.begin() as c:
            c.execute(text("LOCK TABLE jarvis.base_assignments IN EXCLUSIVE MODE"))
            for r in rows:
                if not r.get("evidence", "").strip():
                    raise ValueError("Cada vigência exige evidência documental.")
                from datetime import date

                if date.fromisoformat(r["valid_to"]) < date.fromisoformat(
                    r["valid_from"]
                ):
                    raise ValueError("Vigência invertida.")
                conflict = c.execute(
                    text(
                        "SELECT 1 FROM jarvis.base_assignments WHERE base_code=:base_code AND valid_from<=:valid_to AND valid_to>=:valid_from"
                    ),
                    r,
                ).first()
                if conflict:
                    raise ValueError("Vigência sobreposta: " + r["base_code"])
                c.execute(
                    text(
                        "INSERT INTO jarvis.base_assignments (base_code,base_name,manager,regional,valid_from,valid_to,evidence) VALUES (:base_code,:base_name,:manager,:regional,:valid_from,:valid_to,:evidence)"
                    ),
                    r,
                )
            db.record(c, None, "assignments_imported", details={"count": len(rows)})
        print("Vigências importadas:", len(rows))
    else:
        from datetime import timedelta
        from .db import now

        with db.engine.connect() as c:
            rows = c.execute(
                select(db.conversations.c.id).where(
                    db.conversations.c.created_at
                    < now() - timedelta(days=s.retention_days)
                )
            ).all()
        print(
            "Conversas candidatas à retenção:",
            len(rows),
            "Nenhuma exclusão realizada. Revisar com responsável.",
        )


if __name__ == "__main__":
    main()
