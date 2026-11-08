from sqlalchemy import text


def check_public_writes(engine):
    with engine.connect() as c:
        rows = c.execute(
            text(
                """SELECT n.nspname,c.relname FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
          WHERE n.nspname='public' AND c.relkind IN ('r','p','v','m','f')
          AND has_table_privilege(current_user,c.oid,'INSERT,UPDATE,DELETE,TRUNCATE,TRIGGER')"""
            )
        ).all()
        role = c.execute(
            text(
                "SELECT rolsuper,rolcreaterole,rolcreatedb FROM pg_roles WHERE rolname=current_user"
            )
        ).first()
        create = c.execute(
            text("SELECT has_schema_privilege(current_user,'public','CREATE')")
        ).scalar()
        if rows or any(role) or create:
            raise ValueError(
                "Credencial com privilégios operacionais excessivos. Revise grants diretos, herdados e PUBLIC com o DBA."
            )
