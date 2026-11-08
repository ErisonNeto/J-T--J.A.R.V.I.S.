-- Run once as PostgreSQL administrator. Set passwords interactively with psql \password.
BEGIN;
CREATE ROLE jarvis_memory LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT;
CREATE ROLE jarvis_reader LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT;
REVOKE ALL ON SCHEMA jarvis FROM PUBLIC;
REVOKE ALL ON ALL TABLES IN SCHEMA jarvis FROM PUBLIC;
GRANT USAGE ON SCHEMA jarvis TO jarvis_memory,jarvis_reader;
GRANT SELECT,INSERT,UPDATE ON jarvis.users,jarvis.conversations,jarvis.messages,jarvis.memories TO jarvis_memory;
GRANT SELECT,INSERT ON jarvis.memory_revisions,jarvis.audit,jarvis.investigations TO jarvis_memory;
GRANT SELECT ON jarvis.base_assignments TO jarvis_reader;
GRANT USAGE ON SCHEMA public TO jarvis_reader;
-- Only tables actually present receive SELECT. Never grant all future operational tables.
DO $$ DECLARE t text; BEGIN
 FOREACH t IN ARRAY ARRAY['entregas','t0_diario','capotamento_diario','shipping_time_diario',
 'sem_mov_retidos_detalhe','jt_1bd_registros','jt_5cd_registros','jt_1bd_gestao','jt_arbitragem_ocorrencias'] LOOP
 IF to_regclass('public.'||t) IS NOT NULL THEN EXECUTE format('GRANT SELECT ON TABLE public.%I TO jarvis_reader',t); END IF;
 END LOOP;
END $$;
ALTER ROLE jarvis_reader SET default_transaction_read_only=on;
ALTER ROLE jarvis_reader SET statement_timeout='12s';
ALTER ROLE jarvis_memory SET statement_timeout='12s';
INSERT INTO jarvis.schema_migrations(version) VALUES (3);
COMMIT;
-- IMPORTANT: PostgreSQL roles inherit grants to PUBLIC. Run scripts/check_permissions.py
-- before deployment. Remediate PUBLIC write/create grants with DBA review, not broad automated revokes.
