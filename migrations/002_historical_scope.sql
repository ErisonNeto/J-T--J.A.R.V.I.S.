BEGIN;
-- An administrator must supply documented historical assignments. No fabricated seed data.
CREATE TABLE jarvis.base_assignments (
 base_code varchar(40) NOT NULL,
 base_name varchar(160) NOT NULL,
 manager varchar(120) NOT NULL,
 regional varchar(160) NOT NULL,
 valid_from date NOT NULL,
 valid_to date NOT NULL,
 evidence text NOT NULL CHECK (length(trim(evidence))>0),
 PRIMARY KEY (base_code,valid_from),
 CHECK (valid_to>=valid_from)
);
CREATE INDEX base_assignments_scope ON jarvis.base_assignments(regional,valid_from,valid_to);
-- Serialized validation avoids overlaps even for direct admin writes; no extension required.
CREATE FUNCTION jarvis.guard_assignment() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 PERFORM pg_advisory_xact_lock(hashtext(NEW.base_code));
 IF EXISTS (SELECT 1 FROM jarvis.base_assignments a WHERE a.base_code=NEW.base_code
 AND a.valid_from<=NEW.valid_to AND a.valid_to>=NEW.valid_from
 AND (TG_OP='INSERT' OR (a.base_code,a.valid_from) IS DISTINCT FROM (OLD.base_code,OLD.valid_from))) THEN
 RAISE EXCEPTION 'Overlapping historical assignment';
 END IF;
 RETURN NEW;
END; $$;
CREATE TRIGGER guard_assignment BEFORE INSERT OR UPDATE ON jarvis.base_assignments
 FOR EACH ROW EXECUTE FUNCTION jarvis.guard_assignment();
INSERT INTO jarvis.schema_migrations(version) VALUES (2);
COMMIT;
