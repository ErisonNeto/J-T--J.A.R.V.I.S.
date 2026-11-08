-- 001: run as migration owner, never the application role.
BEGIN;
CREATE SCHEMA IF NOT EXISTS jarvis;
CREATE TABLE IF NOT EXISTS jarvis.schema_migrations (version integer PRIMARY KEY, applied_at timestamptz NOT NULL DEFAULT now());

CREATE TABLE jarvis.users (
	id VARCHAR(36) NOT NULL, 
	name VARCHAR(120) NOT NULL, 
	role VARCHAR(20) NOT NULL, 
	token_hash VARCHAR(64) NOT NULL, 
	active BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE, 
	PRIMARY KEY (id), 
	UNIQUE (token_hash)
)

;

CREATE TABLE jarvis.audit (
	id VARCHAR(36) NOT NULL, 
	actor_id VARCHAR(36), 
	action VARCHAR(80) NOT NULL, 
	target VARCHAR(80), 
	details JSON NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(actor_id) REFERENCES jarvis.users (id)
)

;
CREATE INDEX ix_jarvis_audit_created_at ON jarvis.audit (created_at);

CREATE TABLE jarvis.conversations (
	id VARCHAR(36) NOT NULL, 
	user_id VARCHAR(36) NOT NULL, 
	title VARCHAR(120) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES jarvis.users (id)
)

;
CREATE INDEX ix_jarvis_conversations_user_id ON jarvis.conversations (user_id);

CREATE TABLE jarvis.investigations (
	id VARCHAR(36) NOT NULL, 
	actor_id VARCHAR(36) NOT NULL, 
	city VARCHAR(120) NOT NULL, 
	start VARCHAR(10) NOT NULL, 
	"end" VARCHAR(10) NOT NULL, 
	result JSON NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(actor_id) REFERENCES jarvis.users (id)
)

;

CREATE TABLE jarvis.memories (
	id VARCHAR(36) NOT NULL, 
	author_id VARCHAR(36) NOT NULL, 
	base_code VARCHAR(40) NOT NULL, 
	indicator VARCHAR(30) NOT NULL, 
	occurred_on VARCHAR(10) NOT NULL, 
	explanation TEXT NOT NULL, 
	status VARCHAR(30) NOT NULL, 
	evidence JSON NOT NULL, 
	actions TEXT NOT NULL, 
	outcome TEXT NOT NULL, 
	metrics JSON NOT NULL, 
	version INTEGER NOT NULL, 
	confirmed_by VARCHAR(36), 
	confirmed_at TIMESTAMP WITH TIME ZONE, 
	created_at TIMESTAMP WITH TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(author_id) REFERENCES jarvis.users (id), 
	FOREIGN KEY(confirmed_by) REFERENCES jarvis.users (id)
)

;
CREATE INDEX ix_jarvis_memories_occurred_on ON jarvis.memories (occurred_on);
CREATE INDEX ix_jarvis_memories_base_code ON jarvis.memories (base_code);

CREATE TABLE jarvis.memory_revisions (
	id VARCHAR(36) NOT NULL, 
	memory_id VARCHAR(36) NOT NULL, 
	actor_id VARCHAR(36) NOT NULL, 
	snapshot JSON NOT NULL, 
	reason TEXT NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(memory_id) REFERENCES jarvis.memories (id), 
	FOREIGN KEY(actor_id) REFERENCES jarvis.users (id)
)

;
CREATE INDEX ix_jarvis_memory_revisions_memory_id ON jarvis.memory_revisions (memory_id);

CREATE TABLE jarvis.messages (
	id VARCHAR(36) NOT NULL, 
	conversation_id VARCHAR(36) NOT NULL, 
	role VARCHAR(20) NOT NULL, 
	content TEXT NOT NULL, 
	payload JSON NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(conversation_id) REFERENCES jarvis.conversations (id)
)

;
CREATE INDEX ix_jarvis_messages_conversation_id ON jarvis.messages (conversation_id);
ALTER TABLE jarvis.users ADD CONSTRAINT users_role CHECK (role IN ('admin','manager','analyst','developer'));
ALTER TABLE jarvis.memories ADD CONSTRAINT memories_status CHECK (status IN ('hypothesis','confirmed','rejected'));
ALTER TABLE jarvis.memories ADD CONSTRAINT confirmation_evidence CHECK (status != 'confirmed' OR (confirmed_by IS NOT NULL AND confirmed_at IS NOT NULL));
INSERT INTO jarvis.schema_migrations(version) VALUES (1);
COMMIT;